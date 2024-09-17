import yaml
import csv
import re
import click
import json
import numpy as np
from math import log2, ceil
from mergedeep import merge, Strategy


class HexInt(int):
    pass


def representer(dumper, data):
    return yaml.ScalarNode("tag:yaml.org,2002:int", "0x{:04x}".format(data))


yaml.add_representer(HexInt, representer)


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def fix_block_name(name):
    new_name = name
    new_name = new_name.replace("Mfc", "")
    new_name = new_name.replace("ChErr12", "ChErr")
    new_name = new_name.replace("MiscErrCntSingle", "EccErr")
    new_name = new_name.replace("MiscErrCntDouble", "EccErr")
    new_name = new_name.replace("MiscErrCntParity", "EccErr")
    new_name = new_name.replace("Erx", "ERx")
    new_name = new_name.replace("Etx", "ETx")
    return new_name


def fix_doc_name(name):
    new_name = name
    new_name = new_name.replace("Cal_cal", "Cal")
    new_name = new_name.replace("AlgoDroplsb_drop_lsb", "AlgoDroplsb")
    new_name = re.sub(r"Mux_([^_]+)_select", r"Mux_\1", new_name)
    new_name = re.sub(r"AlgoThreshold_([^_]+)_val", r"AlgoThreshold_\1", new_name)
    new_name = re.sub(r"Cal_([^_]+)_cal", r"Cal_\1", new_name)
    return new_name


def fix_param_name(name):
    """
    Parse and abbreviate parameter names.
    Fixes all caps.

    :param name: Parameter name to be fixed
    :type name: str
    """
    new_name = name

    # remove config or status from name
    new_name = new_name.replace("config_", "")
    if (
        not "phaseSelect" in name
    ):  # exception for phaseSelect, which has RO status and RW value
        new_name = new_name.replace("_status_", "_")

    # fix names of encoder registers
    m_ae = re.compile("Encoder_(\d*)_weights_byte(\d*)")
    if m_ae.match(new_name):
        v0, v1 = m_ae.match(new_name).groups()
        new_name = f"Encoder_weights_{v0}_{v1}"
    if "Encoder_[N]_weights_byte" in new_name:
        new_name = "Encoder_weights_[M]_[N]"

    new_name = new_name.replace("fromMemToLJCDR_", "")
    new_name = new_name.replace("fromFrameAligner_", "")
    new_name = new_name.replace("_CO", "_co")

    new_name = camel_to_snake(new_name)
    new_name = new_name.replace("_config", "config")
    new_name = new_name.replace("pre_l1_a_offset", "pre_l1a_offset")
    return new_name


def expand_param_map(config):
    """
    Create new dictionary with all fields.

    :param config: Original config with compressed registers
    :type config: dict
    """
    # number of inputs that share register and block names if *INPUT is present
    num_inputs = config["ninput"]
    # number of outputs that share register and block names if * is present
    num_outputs = config["noutput"]

    keys_to_discard = ["n_iterations", "addr_shift", "addr_offset"]

    full_config = {}

    for access, access_dict in config.items():
        if not isinstance(access_dict, dict):
            continue
        for block, block_dict in access_dict.items():
            for register, register_dict in block_dict["registers"].items():
                base_address = (
                    (
                        block_dict["addr_base"]
                        + (
                            register_dict["addr_offset"]
                            if "addr_offset" in register_dict
                            else 0
                        )
                    )
                    if "addr_base" in block_dict
                    else 0
                )
                size_byte = (
                    register_dict["size_byte"] if "size_byte" in register_dict else 1
                )
                values = register_dict["value"] if "value" in register_dict else None
                register_name = register

                if "*" in register:
                    # expand shared blocks * with same register names
                    n_iterations = (
                        register_dict["n_iterations"]
                        if "n_iterations" in register_dict
                        else 0
                    )
                    block_names = [block for i in range(n_iterations)]
                    block_ids = [i for i in range(n_iterations)]
                    registers = [
                        register_name.replace("*", "") for i in range(n_iterations)
                    ]
                    addr_shift = register_dict["addr_shift"]
                    register_doc_name = register_name
                    block_doc_name = block
                elif "*" in block:
                    # expand shared registers * with same block names
                    n_channels = num_inputs if "*INPUT" in block else num_outputs
                    block_names = [
                        block.replace("*", "").replace("INPUT", "")
                        for i in range(n_channels)
                    ]
                    block_ids = [i for i in range(n_channels)]
                    registers = [
                        register_name.replace("*", f"{i}") for i in range(n_channels)
                    ]
                    addr_shift = block_dict["block_shift"]
                    values = [values] * n_channels
                    register_doc_name = register_name.replace("*", "[N]")
                    block_doc_name = (
                        block.replace("*INPUT", "[N]")
                        if "*INPUT" in block
                        else block.replace("*", "[N]")
                    )
                else:
                    block_names = [block]
                    block_ids = ["Global"]
                    registers = [register_name]
                    addr_shift = 0
                    values = [values]
                    register_doc_name = register_name
                    block_doc_name = block

                for i, register_ in enumerate(registers):
                    register_address = base_address + i * addr_shift
                    block_name = fix_block_name(block_names[i])
                    block_id = block_ids[i]
                    block_doc_name = fix_block_name(block_doc_name)
                    register_ = fix_param_name(register_)
                    register_doc_name = fix_param_name(register_doc_name)

                    if "params" not in register_dict.keys():
                        max_value = 2 ** (size_byte * 8) - 1
                        bits = 8 * size_byte
                        loc = f"x[{bits-1}:0]"

                        if "*" in register or "*" in block:
                            param_name = f"{block_name}_{i:02d}_{register_}"
                        else:
                            param_name = f"{block_name}_{register_}"
                        param_name = fix_doc_name(param_name)
                        doc_name = fix_doc_name(f"{block_doc_name}_{register_doc_name}")

                        # print(access, block_name, block_id, register_, doc_name, param_name)

                        full_config[param_name] = {
                            "info": [access, block_name, block_id, register_],
                            "address": register_address,
                            "size_byte": size_byte,
                            "default_value": values[i],
                            "max_value": max_value,
                            "param_mask": max_value,
                            "param_shift": 0,
                            "bits": loc,
                            "doc_name": f"{block_doc_name}_{register_doc_name}",
                        }
                    else:
                        max_value = 0
                        for param, param_dict in register_dict["params"].items():
                            shift = param_dict["param_shift"]
                            mask = param_dict["param_mask"]
                            max_value |= ((2**mask - 1) & mask) << shift
                            param_value = (values[i] >> shift) & mask
                            bits = max(ceil(log2(mask)), 1)
                            if bits == 1:
                                loc = f"x[{shift}]"
                            else:
                                loc = f"x[{bits+shift-1}:{shift}]"

                            param = fix_param_name(param)
                            if "*" in register or "*" in block:
                                param_name = f"{block_name}_{i:02d}_{param}"
                            else:
                                param_name = f"{block_name}_{param}"
                            param_name = fix_doc_name(param_name)
                            doc_name = fix_doc_name(f"{block_doc_name}_{param}")

                            # print(access, block_name, block_id, param, doc_name, param_name)

                            full_config[param_name] = {
                                "info": [access, block_name, block_id, param],
                                "address": register_address,
                                "size_byte": size_byte,
                                "default_value": param_value,
                                "max_value": mask,
                                "param_mask": mask,
                                "param_shift": shift,
                                "bits": loc,
                                "doc_name": f"{block_doc_name}_{param}",
                            }

    return full_config


@click.command()
@click.argument(
    "cfg",
    type=click.File("r"),
    default="econ/ECONT_P1_regmap.yaml",
    metavar="[yaml configuration file]",
)
@click.argument(
    "outcfg",
    type=click.File("w"),
    default="ECONT_I2C_params_regmap.csv",
    metavar="[output csv configuration file]",
)
def main(cfg, outcfg):
    """
    Creates register maps for ECONT:
    - yaml and json files contain translation dictionary.
    - params_regmap.csv file contains full map as a table.
    - regmap.csv contains a table of all register addresses and their default values.

    :param cfg : path to yaml file with register and parameter information
    :type cfg: str
    :param outcfg : filename of output csv configuration file
    :type outcfg: str
    """
    econ = "econ-t"
    try:
        register_map = yaml.safe_load(cfg.read())
    except yaml.YAMLError as err:
        sys.exit("Error reading in the config:\n" + +str(err) + "\nexiting ..")

    try:
        register_map = register_map[econ]
    except:
        sys.exit("Error finding " + econ + " in cfg")

    field_names = [
        "block",
        "block_id",
        "parameter",
        "parameter_name",
        "address",
        "access",
        "size_byte",
        "default_value",
        "param_mask",
        "param_shift",
        "max_value",
    ]
    expanded_register_map = expand_param_map(register_map)

    csv_output = csv.DictWriter(outcfg, fieldnames=field_names)
    csv_output.writeheader()

    rows = {}
    yamlrows = {}
    for parameter_name, parameter_dict in expanded_register_map.items():
        access = parameter_dict["info"][0]
        block = parameter_dict["info"][1]
        block_id = parameter_dict["info"][2]
        parameter = parameter_dict["info"][3]
        address = hex(parameter_dict["address"])
        size_byte = parameter_dict["size_byte"]
        default_value = parameter_dict["default_value"]
        param_mask = parameter_dict["param_mask"]
        param_shift = parameter_dict["param_shift"]
        max_value = parameter_dict["max_value"]

        param_dict = {
            "address": address,
            "access": access,
            "size_byte": size_byte,
            "default_value": default_value,
            "param_mask": param_mask,
            "param_shift": param_shift,
            "max_value": max_value,
            "parameter_name": parameter_name,
        }

        block_id_str = (
            "{:02d}".format(int(block_id)) if block_id != "Global" else block_id
        )
        row = {block: {block_id_str: {parameter: param_dict}}}
        merge(rows, row, strategy=Strategy.TYPESAFE_ADDITIVE)

        small_dict = param_dict.copy()
        del small_dict["parameter_name"]
        small_dict["address"] = HexInt(int(small_dict["address"], 16))
        small_dict["param_mask"] = HexInt(small_dict["param_mask"])

        yamlrow = {block: {block_id: {parameter: small_dict}}}
        merge(yamlrows, yamlrow, strategy=Strategy.TYPESAFE_ADDITIVE)

    for i in sorted(rows):
        for j in rows[i]:
            for k in rows[i][j]:
                row = {
                    "block": i,
                    "block_id": j,
                    "parameter": k,
                }
                row.update(rows[i][j][k])
                csv_output.writerow(row)

    for i in sorted(yamlrows):
        number_of_params = np.array(
            [list(yamlrows[i][j].keys()) for j in yamlrows[i]], dtype="object"
        )
        number_of_params = len(list(np.unique(number_of_params)))
        if number_of_params == 1:
            for j in yamlrows[i]:
                for k in yamlrows[i][j]:
                    yamlrows[i][j] = yamlrows[i][j][k]

    # dump as a yaml
    # (useful for users to know the strucutre of yaml files)
    with open(outcfg.name.replace(".csv", ".yaml"), "w") as outfile:
        yaml.dump(yamlrows, outfile, default_flow_style=False)

    # create map with default values
    from make_defaultmap import make_defaultmap, make_validate_translate_maps

    # make_defaultmap(config_name=outcfg.name)

    # create validation and translation maps
    translation_dict, validation_config = make_validate_translate_maps(config=yamlrows)
    # dump these as json
    # with open(outcfg.name.replace(".csv", "_validate.json"), "w") as outfile:
    #    json.dump(validation_config, outfile)
    with open(outcfg.name.replace(".csv", ".json"), "w") as outfile:
        json.dump(translation_dict, outfile, indent="\t")


if __name__ == "__main__":
    main()
