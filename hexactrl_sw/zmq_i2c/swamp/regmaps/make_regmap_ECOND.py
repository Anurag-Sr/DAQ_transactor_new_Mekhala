import click
import pandas as pd
import numpy as np
import yaml
import re
import json

import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)


class HexInt(int):
    pass


def representer(dumper, data):
    return yaml.ScalarNode("tag:yaml.org,2002:int", "0x{:04x}".format(data))


yaml.add_representer(HexInt, representer)


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def organize_block(block, df):
    """
    Find registers within a block and build a dictionary with the structure:
    register:
      addr_offset
      size_byte
      value
      params:
        param_shift
        param_mask
    """

    # find fields that span multiple bytes, and get sum of field widths
    multi_byte_regs = df["Field Name"].value_counts() > 1
    multi_byte_regs = multi_byte_regs.index[multi_byte_regs.values]
    df.reset_index(inplace=True)

    # if registers are split over multiple bytes, assign it to the lowest word
    for r in multi_byte_regs:
        match_name = df["Field Name"] == r
        x = df[match_name]["Register Name"].values
        match_register_name = df["Register Name"].isin(x)
        first_register_name = df.loc[match_register_name]["Register Name"].values[0]
        df.loc[match_register_name, "Register Name"] = first_register_name

    # build register dictionary
    registers = []
    for r in df["Register Name"].unique()[:]:
        d = df.loc[df["Register Name"] == r].copy()

        # change default value of the multi byte register
        d["Field Reset Value"] = (
            d["Field Reset Value"].apply(int, base=16).astype("uint64")
        )

        all_values = d["Field Reset Value"].values
        widths = d["Field Width"].values
        default_value_byte = 0
        num_bits = 0
        for i, val in enumerate(all_values):
            default_value_byte += int(val) << num_bits
            num_bits += widths[i]

        # this is extremely slow
        # could turn the individual values from np.int64 to int using the int()?
        # or just use uint64?
        if default_value_byte < 0:
            with np.errstate(divide="ignore"):
                default_value_byte = int(
                    np.binary_repr(default_value_byte, width=72), 2
                )
                # default_value_byte = default_value_byte % (1 << num_bits)

        widths = d.groupby("Field Name").sum()["Field Width"]
        d = pd.merge(d, widths, left_on="Field Name", right_index=True)
        d.rename(columns={"Field Width_x": "Field Width"}, inplace=True)
        d["Field Width"] = d["Field Width_y"]
        d.drop("Field Width_y", axis=1, inplace=True)
        isDuplicate = d["Field Name"] == d["Field Name"].shift()
        d = d.drop(d[isDuplicate].index)
        d["Field Offset"] = d["Field Width"].cumsum() - d["Field Width"]
        size_byte = int(d["Field Width"].sum() / 8)

        d["Field Reset Value"] = default_value_byte

        d["size_byte"] = size_byte
        # update register address to the bottom one in the overlapping register field
        d["Register Address"] = d["Register Address"].iloc[0]
        registers.append(d)

    return registers


def drop_from_df(d):
    to_drop = [
        "Register Name",
        "Register Width",
        "Register Reset Value",
        "Register Constraints",
        "Register Custom Type",
        "Field Access",
        "Field is Covered",
        "Field is Reserved",
        "Field is Volatile",
        "Field Constraints",
        "Register Description",
        "addr_base",
        "addr_offset",
    ]
    d.drop(to_drop, axis=1, inplace=True)
    d.rename(
        columns={
            "Register Address": "address",
            "Register Access": "access",
            "Field Name": "parameter",
            "Field Offset": "param_shift",
            "Field Width": "param_mask",
            "Field Reset Value": "default_value",
            "BlockName": "block",
            "Field Description": "description",
        },
        inplace=True,
    )
    blockSimple = (
        d.block.str.replace("_ALL", "")
        .str.replace("RO_", "")
        .str.replace("WO_", "")
        .str.replace("RW_", "")
        .values
    )
    d["block"] = blockSimple

    block = d.block.unique()[0]

    parameter_renaming = {
        "RSVD": "RSVD_",
        "FCmd": "fcmd",
        "I2C_WO_": "",
        "I2C_RW_": "",
        "I2C_RO_": "",
        "FIFO": "_fifo_",
        "xx": "",
        "SubP": "subp",
        "eTX": "etx",
        "eRX": "erx",
        "_Test": "_Test_",
        "_Interface": "_Interface_",
        "kapa": "kappa",
    }
    d.replace(parameter_renaming, regex=True, inplace=True)
    d.parameter = d.parameter.apply(camel_to_snake)
    d.parameter.replace("(?i)" + block + "_", "", regex=True, inplace=True)

    # find block_id in blocks with instances e.g. CHAL_00
    blockInstance = np.array(["Global"] * len(blockSimple))
    for i in range(12):
        x = np.array([f"_{i:02n}" in x for x in blockSimple])
        blockInstance[x] = "{:02d}".format(i)
        blockSimple[x] = [v[:-3] for v in blockSimple[x]]
    d["block"] = blockSimple
    d["block_id"] = blockInstance

    parameter_id_num = d.parameter.str.findall("_(\d+)").explode()
    parameter_id_erx = d.parameter.str.findall("_erx(\d+)").explode()
    parameter_id_roc = d.parameter.str.findall("_roc(\d+)").explode()

    parameter_id = parameter_id_num.combine_first(
        parameter_id_erx.combine_first(parameter_id_roc)
    )
    parameter_id = parameter_id.astype(str).str.zfill(2).replace("nan", np.nan)

    is_global = d["block_id"] == "Global"
    is_paramid = ~pd.isna(parameter_id)
    is_noblockid = d["block"].isin(
        [
            "FCTRL",
            "CLOCKS_AND_RESETS",
            "ROC_DAQ_CTRL",
            "ELINK_PROCESSORS",
            "PINGPONG_SRAM",
            "WATCHDOG",
            "WATCHDOG_SP",
            "WATCHDOG_HAM",
            "FORMATTER_BUFFER",
            "MISC",
        ]
    )

    d["block_id"] = parameter_id.where(
        (is_global & is_paramid) & ~is_noblockid, d["block_id"]
    )
    d["parameter_id"] = parameter_id.where(
        ~(is_global & is_paramid) | is_noblockid, np.nan
    )

    d["parameter"] = (
        d.parameter.str.findall("(\D+)").apply("".join).str.replace("[(.*)_]$", "")
    )
    d.parameter.replace("prbs_en", "prbs28_en", regex=True, inplace=True)
    d.parameter.replace("edge_sel_t", "edge_sel_t1", regex=True, inplace=True)
    d.parameter.replace("l_a_", "l1a_", regex=True, inplace=True)
    d.parameter.replace("ic_snapshot", "i2c_snapshot", regex=True, inplace=True)
    d.parameter.replace(r"_{2,}", "_", regex=True, inplace=True)

    d["parameter_name"] = blockSimple
    d.loc[~(d["block_id"] == "Global"), "parameter_name"] = (
        d.parameter_name + "_" + d.block_id
    )
    d.parameter_name = d.parameter_name + "_" + d.parameter
    d.loc[~pd.isna(d.parameter_id), "parameter_name"] = (
        d.parameter_name + "_" + d.parameter_id.astype(str)
    )

    # check size byte
    if (d["size_byte"] > 16).any():
        print("WARNING! size byte is more than 16")
        print(d.loc[d["size_byte"] > 16])

    d["param_mask"] = (2 ** d.param_mask.astype("object")) - 1
    d["max_value"] = d.param_mask

    d.loc[d["size_byte"] > 0, "default_value"] = d.apply(
        lambda x: (int(x.default_value) >> int(x.param_shift)) & int(x.param_mask),
        axis=1,
    ).astype("object")

    return d


def merge_maps_regs(df_maps, df_regs):
    df_maps["BlockMap Instance Name"] = np.array(
        [v[:-4] for v in df_maps["BlockMap Instance Name"].values]
    )

    # repeated groups in df_regs (_xx)
    repeated_groups = []
    for x in df_regs["Register Name"]:
        if ("_xx_ALL" in x) and not (x in repeated_groups):
            repeated_groups.append(x)

    # set index
    df_maps.set_index("BlockMap Instance Name", inplace=True)
    df_regs.set_index("Register Name", inplace=True)

    # replace _xx in register name by 12 eRx
    a = df_regs.loc[repeated_groups].reset_index()
    values = []
    for i in range(12):
        values.append(a.copy())
        values[-1]["Register Name"] = a["Register Name"].str.replace(
            "xx_ALL", f"{i:02n}_ALL"
        )

    # concatenate all registers
    full_regs = pd.concat(values + [df_regs.drop(repeated_groups).reset_index()])
    full_regs.set_index("Register Name", inplace=True)
    full_regs["Register Address"] = df_maps["BlockMap Instance Address"]
    full_regs.sort_values("Register Address", inplace=True)

    # block name
    block_name = full_regs.index.values
    block_name = [x.split("_w")[0] for x in block_name]

    full_regs["BlockName"] = block_name
    first = full_regs.BlockName != full_regs.BlockName.shift(1)
    full_regs.loc[first, "addr_base"] = full_regs.loc[first, "Register Address"]
    full_regs.addr_base = full_regs.addr_base.fillna(method="ffill")
    full_regs["addr_offset"] = (
        full_regs["Register Address"].apply(int, base=16)
        - full_regs["addr_base"].apply(int, base=16)
    ).apply(lambda x: f"0x{x:02x}")

    blocks = full_regs.BlockName.unique()

    new_list = []
    for i, b in enumerate(blocks):
        block = b[3:]
        # print(b)
        # very useful for debugging
        # if b == "RW_CHAL_00_ALL":
        df = full_regs.loc[full_regs.BlockName == b].sort_values(
            ["Register Address", "Field Offset"]
        )
        addr_base = df.addr_base[0]
        reg_access = df["Register Access"][0]
        registers = organize_block(b, df)
        registers = drop_from_df(pd.concat(registers))

        new_list.append(registers)

    d = pd.concat(new_list)
    isRSVD = np.array(["rsvd" in x for x in d.parameter])
    cols = "block,block_id,parameter,parameter_id,address,parameter_name,access,size_byte,default_value,param_mask,param_shift,max_value,description".split(
        ","
    )
    block_renaming = {
        "ALIGNER": "Aligner",
        "CHAL": "ChAligner",
        "CHEPRXGRP": "ChEprxGrp",
        "CHERR": "ChErr",
        "CLOCKS_AND_RESETS": "ClocksAndResets",
        "ELINK_PROCESSORS": "ELinkProcessors",
        "EPRXGRP_TOP": "EprxGrpTop",
        "ERRTOP": "ErrTop",
        "ERX": "ERx",
        "ETX": "ETx",
        "FCTRL": "FCtrl",
        "FORMATTER_BUFFER": "FormatterBuffer",
        "MISC": "Misc",
        "TMR_ERR_CNT": "TMRErrCnt",
        "PINGPONG_SRAM": "PingPongSRAM",
        "ROC_DAQ_CTRL": "RocDaqCtrl",
        "WATCHDOG": "Watchdog",
        "_HAM": "Ham",
        "_MISC": "WatchdogMisc",
        "_SP": "SP",
        "_SUBP_CRC": "SubPCRC",
        "_SUBP_EBO": "SubPEBO",
        "_SUBP_HT": "SubPHT",
        "ZESUPPRESS": "ZS",
        "_COMMON": "Common",
        "_M1": "mOne",
    }
    access_renaming = {
        "RW": "rw",
        "RO": "ro",
        "WO": "wo",
    }
    d.replace(block_renaming, regex=True, inplace=True)
    d.replace(access_renaming, inplace=True)
    return d.loc[~isRSVD, cols]


@click.command()
@click.argument(
    "outcfg",
    default="ECOND_I2C_params_regmap.csv",
    metavar="[output csv configuration file]",
)
def main(outcfg):
    """
    Creates register maps for ECOND:
    - yaml and json files contain translation dictionary.
    - params_regmap.csv file contains full map as a table.
    - regmap.csv contains a table of all register addresses and their default values.

    :param outcfg : filename of output csv configuration file
    :type outcfg: str
    """

    regs = f"econ/ECOND_P1_regs.csv"
    maps = f"econ/ECOND_P1_maps.csv"

    df_regs = pd.read_csv(regs)
    df_maps = pd.read_csv(maps)

    df = merge_maps_regs(df_maps, df_regs)
    df.sort_values(by=["block", "block_id", "parameter_id"], inplace=True)
    df.to_csv(outcfg, index=False)

    # very useful for debugging
    # print(df)

    d = df.groupby("block").apply(lambda x: x.set_index("block_id"))
    from nested_dict import nested_dict

    all_rows = nested_dict()
    to_skip = ["parameter_id", "block", "parameter_name", "parameter", "description"]
    for i, row in d.iterrows():
        block = i[0]
        try:
            block_id = int(i[1])
        except:
            block_id = i[1]
        if pd.isna(row.parameter_id):
            for j, jrow in row.iteritems():
                if j in to_skip:
                    continue
                if j == "address":
                    jrow = HexInt(int(jrow, 16))
                if j == "param_mask":
                    jrow = HexInt(jrow)
                all_rows[block][block_id][row.parameter][j] = jrow
        else:
            for j, jrow in row.iteritems():
                if j in to_skip:
                    continue
                if j == "address":
                    jrow = HexInt(int(jrow, 16))
                if j == "param_mask":
                    jrow = HexInt(jrow)
                all_rows[block][block_id][row.parameter][int(row.parameter_id)][
                    j
                ] = jrow

    # dump as a json
    # with open(outcfg.replace(".csv", ".json"), "w") as outfile:
    #    json.dump(all_rows.to_dict(), outfile)

    # dump as a yaml
    with open(outcfg.replace(".csv", ".yaml"), "w") as outfile:
        yaml.dump(all_rows.to_dict(), outfile, default_flow_style=False)

    from make_defaultmap import make_defaultmap, make_validate_translate_maps

    # create map with default values
    # make_defaultmap(outcfg)

    # create validation and translation maps
    translation_dict, validation_config = make_validate_translate_maps(
        config=all_rows.to_dict()
    )
    # dump these as json
    # with open(outcfg.replace(".csv", "_validate.json"), "w") as outfile:
    #    json.dump(validation_config, outfile)
    with open(outcfg.replace(".csv", ".json"), "w") as outfile:
        json.dump(translation_dict, outfile, indent="\t")


if __name__ == "__main__":
    main()
