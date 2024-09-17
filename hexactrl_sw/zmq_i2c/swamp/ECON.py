from swamp.core import Chip,Transport
import swamp.cfgconverter as cfgconverter
import logging
import numpy
import functools
import time
from nested_dict import nested_dict
import sys
import swamp

def memoize(fn):
    """ Readable memoize decorator. """

    fn.cache = {}
    @functools.wraps(fn)
    def inner(inst, *key):
        if key not in fn.cache:
            fn.cache[key] = fn(inst, *key)
        return fn.cache[key]
    return inner

def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")
        return value
    return wrapper_timer

class econ(Chip):
    @timer
    def __init__( self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        """
        Software counterpart of the ECON ASIC to be used with the test
        systems.
        :param name: Name of the ECON
        :type name: str
        """
        path_to_json = swamp.base_path + "/regmaps/ECOND_I2C_params_regmap.json"
        if cfg['path_to_json']:
            path_to_json=cfg['path_to_json']
        self.cfg_converter = cfgconverter.CfgConverter(path_to_json=path_to_json,parent_logger=self.logger)
        
        self.read_size = 16
        self.write_size = 14 # Cannot write 16 data because reg address is 2-byte wide so it takes one extra position in the lpGBT master buffer
        self.cache = None
        self.cache = numpy.zeros(0,int)

        if 'init_config' in cfg.keys():
            init_file = cfg['init_config']
        else:
            if self.address&0x60==0x60:
                init_file = 'configs/init_econd.yaml'
            elif self.address&0x20==0x20:
                init_file = 'configs/init_econt.yaml'
            else:
                self.logger.critical(f'Wrong address for ECON object, expect 0x2* (ECON-T) or 0x6* (ECON-D)')
        with open(init_file) as fin:
            self.init_config=yaml.safe_load(fin)

    # def read_all(self):
    #     """
    #     Read all of the I2C registers from start to finish and return a bytes
    #     object.  The bytes object can be converted to a dictionary using the
    #     `bytes_to_ECON_dict` method if needed.
    #     """
    #     try:
    #         self.transport.write(
    #             address=self.address,
    #             data=None,
    #             internal_address=(0).to_bytes(2, "big"),
    #             log=False,
    #         )
    #         N = self.cfg_converter.total_length_bytes // self.read_size
    #         Nextra = self.cfg_converter.total_length_bytes % self.read_size
    #         data_that_we_read = []
    #         for i in range(N):
    #             data_that_we_read.append(
    #                 self.transport.read(
    #                     address=self.address, count=self.read_size, log=False
    #                 )
    #             )
    #         if Nextra > 0:
    #             data_that_we_read.append(
    #                 self.transport.read(
    #                     address=self.address, count=Nextra, log=False
    #                 )
    #             )
    #         return b"".join(data_that_we_read)
    #     except OSError:
    #         return b"\x00" * self.cfg_converter.total_length_bytes

    # def write_all(self, data):
    #     """
    #     Write to all of the I2C registers start to finish.  The `data`
    #     parameter must be a bytes object with length equal to
    #     self.cfg_converter.total_length_bytes.  This may be constructed by
    #     passing a dictionary containing all register values to
    #     self.ECON_dict_to_bytes.
    #     """
    #     N = self.cfg_converter.total_length_bytes // self.write_size
    #     Nextra = self.cfg_converter.total_length_bytes % self.write_size

    #     for i in range(N + 1 * (Nextra > 0)):
    #         for attempt in range(3):
    #             try:
    #                 self.transport.write(
    #                     address=self.address,
    #                     data=data[self.write_size * i : self.write_size * (i + 1)],
    #                     internal_address=(self.write_size * i).to_bytes(2, "big"),
    #                 )
    #             except OSError:
    #                 self.logger.debug(
    #                     f"Failed on attempt {attempt} at write {i} of {N}."
    #                 )
    #                 print(f"Failed on attempt {attempt} at write {i} of {N}.")
    #                 if attempt >= 2:
    #                     raise
    #             else:
    #                 break

    def read_some(self, mask_array):
        """
        Read only the I2C registers corresponding to non-zero values in
        mask_array.
        mask_array is a numpy array of dtype numpy.uint8
        Its length must be equal to self.cfg_converter.total_length_bytes
        Return a numpy array of dtype numpy.uint8 with length equal to
        self.total_length_bytes, with non-zero values only where mask_array was
        nonzero.

        This is intended for internal use. The `self.read` method provides a
        more user-friendly interface.
        """
        numpy.set_printoptions(threshold=sys.maxsize)
        try:
            pos = 0
            out_array = numpy.zeros(
                self.cfg_converter.total_length_bytes, dtype=numpy.uint8
            )
            if self.cache.size == 0:
                self.cache = numpy.zeros(
                    self.cfg_converter.total_length_bytes, dtype=numpy.uint8
                )
            while any(mask_array[pos:] != 0):
                start = mask_array[pos:].nonzero()[0][0]
                end = mask_array[pos + start : pos + start + self.read_size].nonzero()[
                    0
                ][-1]
                # if start != 0 or pos == 0:
                reg_address = start+pos
                self.logger.debug(f'read bus addr, reg addr, len = ({self.address}, {reg_address}, {end+1})')
                reg_address = int( (reg_address>>8)&0xFF | (reg_address&0xFF)<<8 ) #invert endianess as needed by lpgbt
                dat = self.transport.read_regs(
                    address=self.address,
                    reg_address_width=2,
                    reg_address=reg_address,
                    read_len=int(end)+1
                )
                out_array[pos + start : pos + start + end + 1] = dat
                self.cache[pos + start : pos + start + end + 1] = dat
                pos = pos + start + end + 1
            return out_array & mask_array
        except OSError:
            return numpy.zeros(self.cfg_converter.total_length_bytes, dtype=numpy.uint8)

    def write_some(self, data_array, mask_array, read_first=True, read_from=None):
        """
        Write only the I2C registers corresponding to non-zero values in
        mask_array.
        data_array is a numpy array of dtype numpy.uint8 and length equal to
        self.cfg_converter.total_length_bytes.  It contains the data to be written.
        mask_array is a numpy array of dtype numpy.uint8 and length equal to
        self.cfg_converter.total_length_bytes.  Only I2C registers
        corresponding to nonzero values of mask_array will be written.
        If read_first is True, then any I2C registers corresponding to entries
        in mask_array that are neither 0 nor 0xff will be read first, so that
        the bits in those registers that we are not trying to write can be
        unchanged.  If read_first is False, then be WARNED: we will overwrite
        those bits even though mask_array seems to indicate they will not be
        changed.

        This is intended for internal use. The `self.configure` method provides
        a more user-friendly interface.
        """
        try:
            if read_first:
                if not read_from:
                    pos = 0
                    read_mask_array = numpy.zeros(
                        self.cfg_converter.total_length_bytes, dtype=numpy.uint8
                    )
                    while any(mask_array[pos:] != 0):
                        start = mask_array[pos:].nonzero()[0][0]
                        end = mask_array[
                            pos + start : pos + start + self.write_size
                        ].nonzero()[0][-1]
                        A, B = pos + start, pos + start + end + 1
                        read_mask_array[A:B] = self.cfg_converter.mask_array[A:B]
                        pos = B

                    start_array = self.read_some(read_mask_array)
                else:
                    start_array = self.cfg_converter.bytes_to_array(read_from)
                data_array = (start_array & (~mask_array)) | (data_array & mask_array)

            pos = 0
            while any(mask_array[pos:] != 0):
                start = mask_array[pos:].nonzero()[0][0]
                end = mask_array[pos + start : pos + start + self.write_size].nonzero()[
                    0
                ][-1]
                
                reg_address = pos+start
                reg_vals = data_array[pos + start : pos + start + end + 1].tolist()
                self.logger.debug(f'bus addr, reg addr, reg_vals, len = ({self.address}, {reg_address}, {reg_vals}, {end+1})')
                reg_address=int( (reg_address>>8)&0xFF | (reg_address&0xFF)<<8 )
                self.transport.write_regs(
                    address=self.address,
                    reg_address_width=2,
                    reg_address=reg_address,
                    reg_vals=reg_vals
                )
                self.cache[pos + start : pos + start + end + 1] = data_array[pos + start : pos + start + end + 1]
                pos = pos + start + end + 1
        except OSError:
            pass

    def configure(self, configuration: dict, read_back=False, read_from=None):
        """
        Writes to ECON registers

        :param configuration: Configuration containing values to write
        :type configuration: dict
        :param read_back: Specifies whether to check read written registers
            after writing. Defaults to False
        :type read_back: bool, optional

        :return: The values of parameters read after readback (if
        read_back=True, otherwise list is empty)
        :rtype: dict
        """
        try:
            self.cfg_converter._validate(configuration)
        except KeyError as err:
            raise KeyError(str(err.args[0]) + f" in ECON {self.name}")
        except ValueError as err:
            raise ValueError(str(err.args[0]) + f" in ECON {self.name}")

        data_dict, mask_dict = self.cfg_converter.configuration_to_dicts(configuration)
        data_array, mask_array = self.cfg_converter.dicts_to_arrays(
            data_dict, mask_dict
        )
        if len(self.cache)==0:
            self.cache = numpy.zeros(len(mask_array),int)
        
        self.write_some(data_array, mask_array, read_from=read_from)

        param_readbacks = []
        if read_back:
            param_readbacks = self.read(configuration)

        return param_readbacks

    def read(self, cfg: dict={}, from_cache: bool=False):
        """
        :param cfg: Configuration containing parameters to read
        :type cfg: dict
        :return: The values of parameters read
        :rtype: tuple
        """
        try:
            self.cfg_converter._validate(cfg, read=True)
        except KeyError as err:
            raise KeyError(str(err.args[0]) + f" in ECON {self.name}")
        except ValueError as err:
            raise ValueError(str(err.args[0]) + f" in ECON {self.name}")

        self.logger.debug(f'Configuration to translate {cfg}')

        if from_cache:
            out_dict = self.cfg_converter.bytes_to_ECON_dict(
                self.cfg_converter.array_to_bytes(self.cache)
            )
        elif len(cfg)>0:
            data_dict, mask_dict = self.cfg_converter.configuration_to_dicts(cfg)
            data_array, mask_array = self.cfg_converter.dicts_to_arrays(
                data_dict, mask_dict, use_data=False
            )
            if len(self.cache):
                self.cache = numpy.zeros(len(mask_array),int)
            out_array = self.read_some(mask_array)
            
            out_dict = self.cfg_converter.bytes_to_ECON_dict(
                self.cfg_converter.array_to_bytes(out_array)
            )
        else:
            self.logger.critical(f'Reading from chip all registers in the cache is not yet supported')
            
        ret_dict=nested_dict()
        if len(cfg)>0:
            par_list = self.cfg_converter.dict_to_out_parameters(cfg, out_dict)
            for item in par_list:
                try:
                    out_val=int(item[1])
                except:
                    out_val=int.from_bytes(item[1], byteorder='little')
                if len(item[0])==4:
                    block, subblock, pname,mask = item[0]
                    if pname not in ret_dict[block][subblock].keys():
                        ret_dict[block][subblock][pname]=[]
                    ret_dict[block][subblock][pname].append(out_val)
                elif len(item[0])==3:
                    block, subblock, pname = item[0]
                    ret_dict[block][subblock][pname]=out_val
                elif len(item[0])==2:
                    block, pname = item[0]
                    ret_dict[block][pname]=out_val
                else:
                    self.logger.critical(f'Unexpected data format when reading ECON slow control: {item}')
        else:
            for key,val in out_dict.items():
                keys = key.split('.')
                try:
                    out_val=int(val)
                except:
                    out_val=int.from_bytes(val, byteorder='little')
                if len(keys)==4:
                    block, subblock, pname,mask = keys
                    if pname not in ret_dict[block][subblock].keys():
                        ret_dict[block][subblock][pname]=[]
                    ret_dict[block][subblock][pname].append(out_val)
                elif len(keys)==3:
                    block, subblock, pname = keys
                    ret_dict[block][subblock][pname]=out_val
                elif len(keys)==2:
                    block, pname = keys
                    ret_dict[block][pname]=out_val
                else:
                    self.logger.critical(f'Unexpected data format when reading ECON slow control: {keys}, {val}')
        return ret_dict.to_dict() 

class dummyTransport(Transport):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        self.nwrite=0
        self.nread=0
        self.fout = open('output.txt','w')
        pass
    
    def write_regs(self, address, reg_address_width, reg_address, reg_vals):
        self.nwrite+=1
        self.fout.write(f'writing addr,val : {reg_address},{reg_vals}\n') 

    def read_regs(self, address, reg_address_width, reg_address, read_len):
        self.nread+=read_len
        return [0xca for i in range(read_len)]
    
    def read(self,address):
        self.nread+=1
        self.fout.write(f'reading addr : {address}\n') 
        return 0xca

import yaml
import copy

def main():
    tr  = dummyTransport(name='i2c_w0',cfg={})

    # cfg = {
    #     'path_to_json' : "./regmaps/ECOND_I2C_params_regmap.json",
    #     'address' : 0x67
    # }
    # econd = econ(name='ECON-D',
    #              cfg =cfg
    # )
    # econd.set_transport(tr)
    
    # with open('configs/setup_unicorn_econd.yaml') as fin:
    #     cfg=yaml.safe_load(fin)

    # econd.configure(cfg)

    cfg = {
        'path_to_json' : "./regmaps/ECOND_I2C_params_regmap.json",
        'address' : 0x20
    }
    econd = econ(name='ECON-D',
                 cfg =cfg
    )
    econd.set_transport(tr)
    
    with open('configs/econd_test_config.yaml') as fin:
        cfg=yaml.safe_load(fin)
    econd.configure(cfg)

    with open("output-d.yaml","w") as fout:
        yaml.dump( econd.read(cfg,from_cache=False),fout,indent=4 )

if __name__ == '__main__':
    main()
        
