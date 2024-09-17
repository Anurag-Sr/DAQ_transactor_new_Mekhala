import sys
import click
import logging
import pandas as pd
import csv
import json


def register_from_param_values(
    param_dict, value_key="default_value", prev_param_value=0
):
    """
    Convert parameter values (from config dictionary) into register value.
    Here, all of the parameters share the same register's address.

    : param param_dict: Dictionary with parameter mask, shift and value
    : type dict
    : param value_key: Key of param_dict that contains the parameter's value
    : type str
    : param prev_param_value: Previous value of register
    : type int
    """
    reg_value = prev_param_value
    for par, rdict in param_dict.items():
        param_val = int(rdict[value_key]) & int(rdict["param_mask"])
        param_val <<= int(rdict["param_shift"])
        reg_value |= param_val
    return reg_value


def make_validate_translate_maps(config):
    """
    Uses full register map (config) to write translation and validation maps
    - The translation dict contains the translator data (in dictionary):
      - access
      - address
      - default_value
      - max_value
      - param_mask
      - param_shift
      - size_byte
    - The validation dict contains (in list):
      - min value of register (by default 0)
      - max value of register
      - register access

    :param config: the full configuration dictionary (as saved in the yaml file)
    :type config: dict
    :return The translation and validation configs
    :rtype (dict,dict)
    """

    translation_dict = {}
    validation_config = {}

    for block in config.keys():
        translation_dict[block] = {}
        validation_config[block] = {}
        for key in config[block].keys():
            if "address" in config[block][key].keys():
                try:
                    parameter = f"{int(key):02d}"
                except:
                    parameter = key
                translator_data = config[block][key]
                translation_dict[block][parameter] = translator_data
                validation_config[block][parameter] = (
                    0,
                    translator_data["max_value"],
                    translator_data["access"],
                )
            else:
                try:
                    instance = f"{int(key):02d}"
                except:
                    instance = key
                translation_dict[block][instance] = {}
                validation_config[block][instance] = {}
                for parameter in config[block][key].keys():
                    if "address" in config[block][key][parameter].keys():
                        translator_data = config[block][key][parameter]
                        translation_dict[block][instance][parameter] = translator_data
                        validation_config[block][instance][parameter] = (
                            0,
                            translator_data["max_value"],
                            translator_data["access"],
                        )
                    else:
                        translation_dict[block][instance][parameter] = {}
                        validation_config[block][instance][parameter] = {}
                        for ikey in config[block][key][parameter].keys():
                            try:
                                parameter_id = f"{int(ikey):02d}"
                            except:
                                parameter_id = ikey
                            translator_data = config[block][key][parameter][ikey]
                            translation_dict[block][instance][parameter][
                                parameter_id
                            ] = translator_data
                            validation_config[block][instance][parameter][
                                parameter_id
                            ] = (
                                0,
                                translator_data["max_value"],
                                translator_data["access"],
                            )

    return translation_dict, validation_config


def make_defaultmap(config_name):
    """
    Read in CSV file with register map and write a map of all the possible register addresses and their default values.

    :config_name: path to CSV file with full list of registers
    :type: str
    """

    logging.basicConfig()

    pattern = "I2C_params_regmap.csv"
    if pattern not in config_name:
        logging.error(f"Filename does not match pattern {pattern}")

    config_table = pd.read_csv(config_name)

    # dictionary where all possible register addresses and their values will be stored
    cache = {}
    config_table["address"] = config_table["address"].apply(int, base=16)
    for address in config_table["address"]:
        subtable = config_table[config_table["address"] == address].to_dict("index")
        value = register_from_param_values(subtable)
        cache[address] = value

    # save as csv
    fname = config_name.replace("_params_regmap.csv", "_default_regmap.json")
    with open(fname, "w") as outfile:
        json.dump(cache, outfile)
    logging.info(
        f"Saved map of default values of registers from parameter values as {fname}"
    )


@click.command()
@click.option("--config_name", required=True, help="CSV file")
def main(config_name):
    """
    Read in CSV file with register map and write a map of all the possible register addresses and their default values.

    :config_name: path to CSV file with full list of registers
    :type: str
    """
    make_defaultmap(config_name)


if __name__ == "__main__":
    sys.exit(main())
