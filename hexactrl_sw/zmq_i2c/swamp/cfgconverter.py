from typing import Dict, List, Tuple
import numpy as np
import re
import logging
import pathlib
import json
import yaml
import bitstruct.c as bitstruct
import swamp

regmap_to_path = {
    "ECONT": [
        # full register map in CSV form (with parameter names)
        "ECONT_I2C_params_regmap.csv",
        # full register map in JSON form (with parameter names)
        "ECONT_I2C_params_regmap.json",
    ],
    "ECOND": [
        "ECOND_I2C_params_regmap.csv",
        "ECOND_I2C_params_regmap.json",
    ],
}


def retrieve_regmap_path(target, relative_path=swamp.base_path) -> str:
    try:
        if (relative_path / pathlib.Path("regmaps")).is_dir():
            regmap_paths = [
                str((relative_path / pathlib.Path("regmaps", r)).absolute())
                for r in regmap_to_path[target]
            ]
        else:
            regmap_paths = None
    except:
        regmap_paths = None
        p = str((relative_path / pathlib.Path("regmaps", r)).absolute())
        swamp.util.getLogger().error(f"No register maps found for {target} in {p}")

    return regmap_paths


class CfgConverter:
    """
    Provides functions to convert parameter names into readable configs and viceversa
    """

    def __init__(self, path_to_json: str, parent_logger: logging.Logger = None):
        """
        :param path_to_json: Path to JSON file with full information of registers in dictionary format
        :type path_to_json: str
        """
        if parent_logger is None:
            self.logger = logging.getLogger("config-converter")
        else:
            self.logger = parent_logger.getChild("config-converter")

        with open(path_to_json, "r") as json_file:
            self._parse_regmap(json.load(json_file))

        self._setup_bitstruct()

    def _parse_regmap(self, regmap_dict):
        """
        Parse the regmap JSON file containing the full map of registers.
        Sets self.registers, which is a numpy array.
        The first axis indexes individual registers, while the second
        axis indexes data fields. The data fields are:
          0: register name
          1: register size in bits
          2: register position as an offset in bits from the LSB of internal
             address 0
          3: a zero value with the right type (`int` if the bit width is 64 or
             less, `bytes` otherwise)
          4: param_mask, which is a value with all bits 1, and the right type
             (`int` if the bit width is 64 or less, `bytes` otherwise)
          5: the maximum allowed value for the register
          6: the access type: "rw", "ro", or "wo"
        The array is sorted from least to greatest according to field 2, the
        position within the I2C register space
        """
        unsorted_registers = np.array(list(parse_dict(regmap_dict)), dtype="object")
        self.registers = unsorted_registers[np.argsort(unsorted_registers[:, 3])]

        # Construct some dictionaries containing zero, or all-bits-one, or
        # default values, with the appropriate type (unsigned integer or bytes,
        # depending on the size of the register).
        self.zero_dict = {reg[0]: reg[4] for reg in self.registers}
        self.default_value_dict = {reg[0]: reg[5] for reg in self.registers}
        self.mask_dict = {reg[0]: reg[6] for reg in self.registers}
        self.max_value_dict = {reg[0]: reg[7] for reg in self.registers}
        self.access_dict = {reg[0]: reg[8] for reg in self.registers}

    def _setup_bitstruct(self):
        """
        Do all the setup necessary to use bitstruct to convert between the
        `bytes` used and returned by I2C writes and reads and a dictionary.

        The idea is to treat the entire I2C register space as a big bytestring,
        and to set up a means to translate between that bytestring and a
        dictionary mapping named registers to values. The `bitstruct` module
        does exactly this. We just need to create a "format string" that
        describes the size and type of all of the individual registers
        contained within the I2C register space.

        The "format string" contains a sequence of specifiers related to each
        register.  The first character is the type, which is mostly "u" for
        unsigned integer, but is sometimes "r" for a raw bytestring, which we
        use in the case of registers (like the snapshot registers) that are
        larger than 64 bits and cannot fit in an unsigned int. Some are also
        "p" for "padding", which is used to fill in the parts of the register
        space that are empty.

        After the type specifier is a number, which is the number of bits that
        each register occupies.

        To build the format string, we get the entire list of registers by
        parsing the CSV file, and we calculate the absolute bit position of
        each register from its address and param_shift. Then we sort the
        register list by this absolute bit position, and iterate through the
        sorted list. For each register, we calculate whether we need to add a
        "padding" field specifier to separate it from the previously-processed
        register. Then we append the padding specifier, if any, and the
        register's specifier to a list. At the end, we join all of these
        specifiers together to form the format string. Then we compile the
        format string into an object that can efficiently pack and unpack
        between bytes and dictionaries.
        """

        # We start from bit position 0 in the I2C register space. This
        # corresponds to internal address 0 and param_shift 0. If there is no
        # register at internal address 0 and param_shift 0, then the first
        # thing we add to the format string will be a padding specifier.
        # Otherwise, the first thing will be a register specifier.
        pos = 0
        # This list will hold each individual specifier as we construct them by
        # iterating over the list of registers. After the loop, we will join
        # all the elements of this list together to make a single format
        # string.
        fmt_list = []
        for reg in self.registers:
            name = reg[0]
            bits = reg[2]
            position = reg[3]

            # If the size of the register is more than 64 bits, then we cannot
            # use an integer to hold it, and so we use a raw bytestring in that
            # case.
            if bits > 64:
                s = f"r{bits}"
            else:
                s = f"u{bits}"

            # If there is a gap between the end of the previous register and
            # the start of this register, then we add a padding specifier to
            # fill up the space between.
            if position != pos:
                fmt_list.append(f"p{position-pos}")
                # This assertion is here to help us find bugs in the register
                # map CSV file, such as overlapping registers.
                assert position > pos, (pos, reg)
            # After the padding specifier, if any, we add on the actual
            # register specifier.
            fmt_list.append(s)
            # Now we calculate the position of the bit immediately following
            # this register, so that we know whether to add any padding before
            # the next register.
            pos = position + bits

        # After the end of the loop, the entire register space should end at an
        # 8-bit boundary. If it doesn't, we should think about how to add
        # padding to reach an 8-bit boundary.
        assert (pos % 8) == 0

        # Now join the list of specifiers into a single string, and compile a
        # bitstruct packer/unpacker object that will pack/unpack from/to a
        # dictionary. The list of specifiers is reversed first in order to
        # correctly handle the endianness of the ECON I2C register space.
        format_string = "".join(fmt_list[::-1])
        reg_names = list(self.registers[::-1, 0])
        self.compiled_format = bitstruct.compile(format_string, reg_names)

        self.default_value_bytes = self.ECON_dict_to_bytes(self.default_value_dict)

        self.default_value_array = np.frombuffer(self.default_value_bytes, np.uint8)
        self.mask_array = np.frombuffer(
            self.ECON_dict_to_bytes(self.mask_dict), np.uint8
        )

        RW_mask_dict = {
            name: (
                self.mask_dict[name]
                if self.access_dict[name] == "rw"
                else self.zero_dict[name]
            )
            for name in self.registers[:, 0]
        }
        RW_mask_bytes = self.ECON_dict_to_bytes(RW_mask_dict)
        self.RW_mask_array = self.bytes_to_array(RW_mask_bytes)

        total_length_bits = bitstruct.calcsize(format_string)
        assert (total_length_bits % 8) == 0
        self.total_length_bytes = total_length_bits // 8

    def ECON_dict_to_bytes(self, ECON_dict):
        """
        Use the compiled bitstruct object to pack a dictionary into a bytes
        object. All of the register names have to exist in the dictionary. This
        is intended for internal use only, but it might be useful for some
        external use.

        The bytes object is reversed to properly handle the endianness of the
        ECON I2C register space.
        """
        return self.compiled_format.pack(ECON_dict)[::-1]

    def bytes_to_ECON_dict(self, data):
        """
        Use the compiled bitstruct object to unpack a bytes object into a
        dictionary. The size in bytes of the bytes object must be equal to
        self.total_length_bytes, and the dictionary will contain every
        register. This is intended for internal use only, but it might be
        useful for some external use.
        """
        return self.compiled_format.unpack(data[::-1])

    def configuration_to_dicts(self, configuration):
        """
        This takes the "configuration" nested dictionary and converts it to a
        flat dictionary based on the register names described by the keys at
        each level of the nested dictionary.

        It returns two flat dictionaries. One, data_dict, contains the actual
        values from `configuration`. The other, mask_dict, contains
        all-bits-one values suitable for the "mask" needed by write_some and
        read_some.
        """
        data_dict = self.zero_dict.copy()
        mask_dict = self.zero_dict.copy()
        for key, _, value in flatten_dict(configuration):
            data_dict[key] = value
            mask_dict[key] = self.mask_dict[key]
        return data_dict, mask_dict

    def dicts_to_arrays(self, data_dict, mask_dict, use_data=True):
        """
        This takes the flat dictionaries produced by `configuration_to_dicts`
        and converts them to numpy arrays of dtype numpy.uint8 and length equal
        to self.total_length_bytes.
        """
        if use_data:
            data_array = np.frombuffer(self.ECON_dict_to_bytes(data_dict), np.uint8)
        else:
            data_array = np.zeros(self.total_length_bytes, np.uint8)
        mask_array = np.frombuffer(self.ECON_dict_to_bytes(mask_dict), np.uint8)
        return data_array, mask_array

    def bytes_to_array(self, bytes_data):
        """
        This takes a bytes object with total length equal to
        self.total_length_bytes and converts it to a numpy array with dtype
        numpy.uint8.
        """
        return np.frombuffer(bytes_data, np.uint8)

    def array_to_bytes(self, out_array):
        """
        This takes a numpy array of dtype numpy.uint8 and converts it to a
        bytes object.
        """
        return bytes(out_array.data)

    def dict_to_out_parameters(self, configuration, out_dict):
        """
        This takes the flat dictionary produced by self.bytes_to_ECON_dict and
        extracts only the registers that appear in `configuration`, putting
        them into a list.
        """
        out_parameters = []
        for key, key_list, value in flatten_dict(configuration):
            out_parameters.append((key_list, out_dict[key]))
        return out_parameters

    def make_modified_full_configuration(
        self, starting_configuration, config=None, config_name=None, param_names=None
    ):
        """
        This takes a starting configuration (as a bytes object) and a set of
        registers to change.  It returns a new bytes object representing the
        new desired configuration.

        The set of registers to change can be represented in the same ways as
        `econ_i2c.write` accepts inputs. This includes a nested dictionary in
        `config`, a YAML file in `config_name`, or a tuple of parameter names
        and values in `param_names`.  If more than one of `config`,
        `config_name`, and `param_names` are provided, `config` will take
        precedence over `config_name` and `param_names`, and `config_name` will
        take precedence over `param_names`.
        """

        if config is None:
            if config_name:
                with open(config_name, "r") as f:
                    config = yaml.safe_load(f)
            elif param_names:
                parameter_cfg = self.get_parameters_fromparamnames(param_names)
                config = self.get_cfg_fromnames(parameter_cfg)

        flat_dict = self.bytes_to_ECON_dict(starting_configuration)
        for key, _, data in flatten_dict(config):
            assert key in flat_dict
            flat_dict[key] = data

        return self.ECON_dict_to_bytes(flat_dict)

    def _validate(self, configuration: dict, read=False):
        """
        Check whether everything we are attempting to read or write has the
        correct permissions and, if we are writing, that the value to be
        written falls within the allowed bounds.

        :param configuration: A mapping of names to values to be written
        :type configuration: dict
        :param read: Specifies whether we should check for read access or write
            access
        :type read: bool, optional
        """
        for key, _, data in flatten_dict(configuration):
            if read:
                # If we are reading, then we can ignore `data_dict` and
                # only check the access type, which must be "rw" or "ro"
                if self.access_dict[key] == "wo":
                    raise ValueError(f"Trying to read {key}, which is write-only.")
            else:
                # If we are writing, then we need to check the access type,
                # which must be "rw" or "wo", and also check that the value
                # is within the allowed bounds.
                if self.access_dict[key] == "ro":
                    raise ValueError(f"Trying to write {key}, which is read-only.")

                # For registers that are larger than 64 bits, the value is `bytes`
                # instead of an integer, so convert back to an integer here
                if isinstance(data, bytes):
                    data = int.from_bytes(data, "little")

                if data < 0:
                    raise ValueError(
                        f"Trying to write a negative value to {key}. Only unsigned values are allowed."
                    )

                # Same conversion for max_value
                max_value = self.max_value_dict[key]
                if isinstance(max_value, bytes):
                    max_value = int.from_bytes(max_value, "little")

                if data > max_value:
                    raise ValueError(
                        f"Trying to write 0x{data:x} to {key}, but the maximum allowed value is 0x{max_value:x}."
                    )

    def get_parameters_fromparamnames(self, param_names: Tuple):
        """
        Converts a tuple of "Parameter name:Parameter value" into a dictionary
        of {parameter_name: parameter_value}.
        Accepts wild cards in Parameter name and unrolls them.
        Parameter name:Parameter value are given only in the context of writing (no read only)
        Parameter name (without value)  are given only in the context of reading (no write only)

        :param param_names:
        :type param_names: Tuple
        """

        if not isinstance(param_names, tuple):
            raise Exception(
                "Parameter is not given as Tuple. Please provide (str,) if you are proving a single string"
            )

        self.logger.warning("get_parameters_fromparamnames is slow")

        # expand string (":") and wildcards into list of registers
        all_parameter_names = self.registers[:, 0]

        range_finder = re.compile(r"\[(\d+)-(\d+)\]")

        parameter_cfg = {}
        for param in param_names:
            param_split = param.split(":")
            if len(param_split) == 2:
                key = param_split[0]
                value = int(param_split[1], 0)
            elif len(param_split) == 1:
                key = param_split[0]
                value = None
            else:
                raise Exception("Larger number of : expected")

            brackets = [(int(A), int(B)) for A, B in range_finder.findall(key)]
            key_matcher = re.compile(
                range_finder.sub("([0-9]+)", key.replace("*", ".*"))
            )
            for parameter_name in all_parameter_names:
                key_match = key_matcher.fullmatch(parameter_name)
                if key_match is not None:
                    if self.access_dict[parameter_name] == "wo" and value is None:
                        self.logger.debug(f"Skipping wo {parameter_name}")
                        continue
                    if self.access_dict[parameter_name] == "ro" and value is not None:
                        self.logger.debug(f"Skipping ro {parameter_name}")
                        continue
                    if len(brackets) > 0:
                        for i in range(len(brackets)):
                            N = int(key_match.groups()[i])
                            if (N >= brackets[i][0]) and (N <= brackets[i][1]):
                                parameter_cfg[parameter_name] = value
                    else:
                        parameter_cfg[parameter_name] = value

        return parameter_cfg

    def get_parameters_fromcfg(self, cfg):
        """
        Converts a configuration dictionary (that matches structure of
        full-register map yaml file) and has register values, into a dictionary
        of parameter_name and values.
        {'parameter_name': <value>}

        :param cfg: configuration dictionary
        :type cfg: dict
        """

        return {key: value for key, _, value in flatten_dict(cfg)}

    def _params_fromtable_helper(self, key_list, value):
        """
        Helper function for get_parameters_fromtable
        """
        key = ".".join([f"{k:02d}" if isinstance(k, int) else k for k in key_list])
        return (key, [value, self.access_dict[key]])

    def get_parameters_fromtable(self, tables: Tuple[(List[str], int)]):
        """
        Converts a table of the form:
        ([block, block_id, parameter], reg_value)
        or
        ([block, block_id, parameter, parameter_id], reg_value)
        into a dictionary:
        {parameter_name: [reg_value, access])

        :param tables: table of the form [(block, block_id, parameter, parameter_id),reg_value]
        :type tables: list
        """

        return dict([self._params_fromtable_helper(*row) for row in tables])

    def get_cfg_fromnames(self, parameter_cfg: Dict):
        """
        Converts a dictionary of {'parameter_name': <value>} into a configuration dictionary.

        :param parameter_name: dictionary with format {'parameter_name': <value>}
        :type parameter_name: dict
        """

        ret = dict()
        for reg in self.registers:
            name = reg[0]
            key_list = reg[1]
            if name not in parameter_cfg:
                continue
            value = parameter_cfg[name]
            D = ret
            for key in key_list[:-1]:
                if key not in D:
                    D[key] = dict()
                D = D[key]
            D[key_list[-1]] = value
        return ret


def flatten_dict(nested_dict):
    """
    This takes a nested dictionary and flattens it, combining keys with an
    underscore, and also returning the list of nested keys
    """
    for key, val in nested_dict.items():
        if isinstance(key, int):
            formatted_key = f"{key:02d}"
        else:
            formatted_key = key

        if isinstance(val, dict):
            for nested_key, nested_key_list, val in flatten_dict(val):
                yield (f"{formatted_key}.{nested_key}", [key] + nested_key_list, val)
        elif isinstance(val, list):
            for index, nested_value in enumerate(val):
                yield (
                    f"{formatted_key}.{index:02d}",
                    [key] + [f"{index:02d}"],
                    nested_value,
                )
        else:
            yield (formatted_key, [key], val)


def parse_dict(regdict):
    """
    Generator function that takes the nested dictionary from the default json
    file and parses each parameter as
    [register_name, key_list, size, position, zero_value, default_value, mask, max_value, access]
    """
    for key, value in regdict.items():
        try:
            key = int(key)
            formatted_key = f"{key:02d}"
        except:
            formatted_key = key

        if isinstance(value, dict):
            if "default_value" in value:
                size_bits = int(np.log2(value["param_mask"] + 1.0))
                default_value = value["default_value"]
                param_mask = value["param_mask"]
                max_value = value["max_value"]
                zero = int(0)
                if size_bits > 64:
                    default_value = default_value.to_bytes(value["size_byte"], "little")
                    param_mask = param_mask.to_bytes(value["size_byte"], "little")
                    max_value = max_value.to_bytes(value["size_byte"], "little")
                    zero = (0).to_bytes(value["size_byte"], "little")
                position = 8 * value["address"] + value["param_shift"]
                yield [
                    formatted_key,
                    [key],
                    size_bits,
                    position,
                    zero,
                    default_value,
                    param_mask,
                    max_value,
                    value["access"],
                ]
            else:
                for row in parse_dict(value):
                    yield [".".join([formatted_key, row[0]]), [key] + row[1]] + row[2:]
        else:
            raise ValueError(value)
