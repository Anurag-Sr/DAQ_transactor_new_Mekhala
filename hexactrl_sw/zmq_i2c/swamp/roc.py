import os
import re
import time
import functools
from itertools import groupby, count
from operator import itemgetter
import yaml
import pickle
from nested_dict import nested_dict

import swamp
import swamp.util as util
from swamp.core import Chip, Transport


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


def count_bits_at_one(number):
    bits = 0
    shifted_number = number
    while shifted_number > 0:
        bits += shifted_number & 1
        shifted_number = shifted_number >> 1
    return bits


def lsb_position(mask):
    min_bit = 0
    while mask & 1 == 0:
        mask = mask >> 1
        min_bit += 1
    return min_bit


class roc(Chip):
    @timer
    def __init__(self, name : str="", cfg : dict={}):
        super().__init__(name, cfg)
        self.logger.debug("Creating new roc with name: %s", name)
        if 'init_config' in cfg:
            self.logger.debug("Found 'init_config' field: %s", cfg['init_config'])
            with open(cfg['init_config']) as fin:
                self.init_config = yaml.safe_load(fin)
        else:
            self.logger.debug("'init_config' not found, using default configs/init_roc.yaml.")
            with open(os.path.join(swamp.base_path, 'configs/init_roc.yaml')) as fin:
                self.init_config = yaml.safe_load(fin)
        self.regmapfile = os.path.join(swamp.base_path, 'configs/si_hgcroc_map.pickle')
        if 'regmapfile' in cfg:
            self.logger.debug("Found 'regmapfile' field: %s", cfg['regmapfile'])
            self.regmapfile=cfg['regmapfile']
        try:
            self.logger.debug("opening regmap file: %s.", self.regmapfile)
            with open(self.regmapfile, 'rb') as fin:
                self.regmap = pickle.load(fin)
        except Exception as e:
            self.logger.critical(f'Error when trying to load the HGCROC reg map : {self.regmapfile}')
            self.logger.critical(f'Exception : {str(e)}')
            self.logger.critical(f'The process will exit')
            exit(1)
        
        self.prev_addr = (None, None)
        self.logger.info("Done creating ROC: %s", self.name)

    def read(self, cfg: dict={}, from_cache: bool=False):
        self.logger.debug(f'read with config = {cfg}')

        if len(cfg)>0:
            validation = self.__validate(cfg)
            if validation['flag']==False:
                return {
                    'flag':'ERROR',
                    'error_message': f'Configuration error at cfg validation with error \n {validation["error_message"]}'
                }
            valid_cfg = validation['valid_config']        
        
        ret_cfg={}
        if from_cache:
            ret_cfg = self.cfg_from_pairs(self.cache)
        else:
            if not cfg:
                sortedPairs = self.__sort_pairs(self.cache)
            else:
                pairs = self.__pairs_from_cfg(valid_cfg) #pair format : { (R0,R1): val }
                sortedPairs = self.__sort_pairs(pairs)
            ret_pairs = self.__read(sortedPairs)
            self.cache.update(ret_pairs)
            ret_cfg = self.cfg_from_pairs(ret_pairs)
        if len(cfg)>0:
            req_keys = set(key for key in nested_dict(valid_cfg).keys_flat())
            req_cfg = nested_dict()		                        # .. so only return requested config.
            for idx, val in nested_dict(ret_cfg).items_flat():
                if idx in req_keys:       	                    # idx=(block,blockID,param)
                    req_cfg[idx[0]][idx[1]][idx[2]] = val
            ret_cfg=req_cfg.to_dict()
        return ret_cfg

    def configure(self, cfg: dict, read_back : bool=False):
        self.logger.debug(f'Configuring {self.name} with {cfg}')
        validation = self.__validate(cfg)
        if validation['flag']==False:
            return {
                'flag':'ERROR',
                'error_message': 'Configuration error at cfg validation with error \n {validation["error_message"]}'
            }
        valid_cfg = validation['valid_config']
        pairs = self.__pairs_from_cfg(valid_cfg) #pair format : { (R0,R1): val }
        self.cache.update(pairs)
        sortedPairs = self.__sort_pairs(pairs)
        self.__write(sortedPairs)
        self.logger.info(f'{self.name} Configured')
        if read_back:
            cfg = self.read(cfg)
        return cfg
 
    def pll_lock(self):
        val = (self.transport.read(self.address + 0x7) )#& 0x4)>>2
        self.logger.info(f'HGCROC {self.name} PLL lock = {val}')
        return val

    def read_reg(self,R0,R1):
        val = self.__single_read( (R0,R1) )
        pairs = { (R0,R1): val }
        self.cache.update(pairs)
        return val
    
    def write_reg(self,R0,R1,val):
        pairs = { (R0,R1): val }
        self.cache.update(pairs)
        self.__single_write( (R0,R1),val )
    
    def __validate(self,cfg):
        valid_cfg = {}
        for block in cfg:
            valid_cfg[block] = {}
            for blockId,params in cfg[block].items():
                if not isinstance(blockId, int):
                    if blockId == "all":
                        blockIds = [key for key,val in self.regmap[block].items()]
                    elif "," in blockId:
                        blockIds = [int(bid) for bid in blockId.split(",")]
                    elif "-" in blockId:
                        limits = [int(bid) for bid in blockId.split("-")]
                        blockIds = range(limits[0], limits[1]+1)
                    else:
                        self.logger.critical(f'Invalid config :')
                        self.logger.critical(f'cfg[{block}] expects keys as Integers, "all", "Integers-Integers" or "Integers,Integers"')
                        self.logger.critical(f'Given type : {type(blockId)} is forbiden')
                        return {"flag": False, "valid_config": valid_cfg, "error_message": f'Invalid config with wrong blockId type'}

                else: blockIds = [blockId]
                if not all(x in [key for key,val in self.regmap[block].items()] for x in blockIds):
                    self.logger.critical(f'Invalid config :')
                    self.logger.critical(f'{block} does not have the right format')
                    return {"flag": False, "valid_config": valid_cfg, "error_message": f'Invalid config : {block} does not have the right format'}
                for bId in blockIds:
                    valid_cfg[block][bId] = params

            validation_dict = self.__validateRecursively(valid_cfg,self.regmap)
            validation_dict["valid_config"]=valid_cfg
            if validation_dict['flag']==True:
                for block in valid_cfg:
                    for blockId in valid_cfg[block]:
                        for param, paramVal in valid_cfg[block][blockId].items():
                            par_regs = self.__regs_from_regMap(block, blockId, param) #dictionary with all regs handling param
                            max_val = 0
                            for reg_id, reg in par_regs.items():
                                max_val |= reg["param_mask"]
                            if paramVal>max_val:
                                self.logger.critical(f'Invalid config of {block}/{blockId}/{param}/{paramVal}: larger than maximum value of {block}/{blockId}/{param}/{max_val}')
                                return {"flag": False, "error_message": f'Invalid config of {block}/{blockId}/{param}/{paramVal}: larger than maximum value of {block}/{blockId}/{param}/{max_val}'}
        return validation_dict

    def __validateRecursively(self,cfg,regmap):
        for key in cfg:
            if not key in regmap.keys():
                self.logger.critical(f'Invalid config : {key} is not a valid key of the roc register map {self.regmapfile}')
                return {"flag": False, "error_message": f'Invalid config : {key} is not a valid key of the roc register map {self.regmapfile}'}
            elif isinstance(cfg[key], dict):
                return self.__validateRecursively(cfg[key],regmap[key])
        return  {"flag": True, "error_message": ''}
            
    def __pairs_from_cfg(self, cfg):
        """
        Convert an input config dict to addr (R0,R1): value (R2) pairs.
        There is two cases to consider for setting parameter value information:
        Case 1: One parameter value spans several registers. (Ex. IdleFrame)
        Case 2: Several parameter values share same register. (Ex. Delay9, Delay87)
        """
        nread=0
        pairs = {}
        for block in cfg:
            for blockId in cfg[block]:
                for param, paramVal in cfg[block][blockId].items():
                    par_regs = self.__regs_from_regMap(block, blockId, param) #dictionary with all regs handling param
                    for reg_id, reg in par_regs.items():
                        addr = (reg["R0"], reg["R1"])
                        isPartialRegister = (reg['param_mask'] != 0xff)
                        if isPartialRegister:
                            nread+=1
                            if addr in pairs:
                                prev_regVal = pairs[addr]                          # regVal already added
                            elif addr in self.cache:
                                prev_regVal = self.cache[addr]              # regVal already cached/written 
                            else:
                                if self.is_sc_power_on_value:
                                    params_in_reg = self.__params_in_reg(block, blockId, reg)
                                    prev_regVal = self.__get_default_reg_val(params_in_reg)
                                else:
                                    prev_regVal = list(self.__read([[{addr:0}]]).values())[0]
                        else:
                            prev_regVal=0 #if full reg we will overwrite it completely
                        pairs[addr] = self.__regVal_from_paramVal(reg, paramVal, prev_regVal)
        self.logger.debug(f'number of read in pair from cfg = {nread}')
        return pairs

    def cfg_from_pairs(self, pairs):
        """
        Convert from {addr:val} pairs to {param:param_val} config.
        We can only recover a parameter from a pair when it is in the common cache.
        However, when we read (or write) a param the common cache is populated in advance.
        """
        cfg = nested_dict()
        for name, block in self.regmap.items():
            for blockId, params in block.items():
                for pname, param in params.items():
                    for reg_id, reg in param.items():
                        addr = (reg["R0"], reg["R1"])
                        if addr in pairs.keys():
                            prev_regVal = cfg[name][blockId][pname] if cfg[name][blockId][pname]!={} else 0
                            cfg[name][blockId][pname] = self.__paramVal_from_regVal(reg, pairs[addr], prev_regVal)
        return cfg.to_dict()


    @memoize
    def __regs_from_regMap(self, block, blockId, name):
        """ (block, blockId, name) -> (R0, R1, defval_mask, param_mask, param_minbit, reg_mask, reg_id) """

        return self.regmap[block][blockId][name]

    def __params_in_reg(self, block, blockId, reg):
        """ (block, blockId, reg) -> list of regs with same R0 and R1 """
        regs=[]
        for name in self.regmap[block][blockId]:
            for _, param in self.regmap[block][blockId][name].items():
                if param['R0']==reg['R0'] and param['R1']==reg['R1']:
                    regs.append(param)
        return regs

    def __get_default_reg_val(self, params_in_reg):
        """ (list of params with same 'R0' 'R1') -> default param value """
        reg_value=0
        for par in params_in_reg:
            reg_value |= par['defval_mask']
        return reg_value
            
    def __regVal_from_paramVal(self, reg, param_value, prev_reg_value=0):
        """ Convert parameter value (from config) into register value (1 byte). """
        reg_value = param_value & reg["param_mask"]
        reg_value >>= util.get_lsb_id(reg["param_mask"])
        reg_value <<= util.get_lsb_id(reg["reg_mask"])
        inv_mask = 0xff - reg["reg_mask"]
        reg_value = (prev_reg_value & inv_mask) | reg_value
        return reg_value
        
    def __paramVal_from_regVal(self, reg, reg_value, prev_reg_value=0):
        """ Convert register value into (part of) parameter value. """
        param_val = reg_value & reg["reg_mask"]
        param_val >>= util.get_lsb_id(reg["reg_mask"])
        param_val <<= util.get_lsb_id(reg["param_mask"]) 
        param_val += prev_reg_value
        return param_val

    def __sort_pairs(self, pairs):
        """ Sort pairs by same R0 and consecutive R1 """
        addrs = pairs.keys()
        addrs = sorted(addrs, key=itemgetter(0))
        addrs = sorted(addrs, key=itemgetter(1))
        sortedAddrs = [list(g) for k, g in groupby(addrs, key=lambda addr, c=count(): complex(addr[0]-next(c), addr[1]))]
        sortedPairs = [[{addr: pairs[addr]} for addr in subList] for subList in sortedAddrs]
        return sortedPairs

    def __write(self,sortedpairs):
        #pairs format = {(R0,R1): val}
        for subList in sortedpairs:
            addr = list(subList[0].keys())[0]
            if len(subList) > 1:        # burst-write for grouped pairs
                vals = [v for pair in subList for k, v in pair.items()]
                self.__burst_write(addr, vals)
            else:
                self.__single_write(addr, subList[0][addr])
        
    def __single_write(self, addr, val):
        """ Write parameter value (to R2). """
        if addr[0] != self.prev_addr[0]: self.transport.write(self.address,     addr[0])
        if addr[1] != self.prev_addr[1]: self.transport.write(self.address + 1, addr[1])
        self.transport.write(self.address + 2, val)
        self.prev_addr = addr

    def __burst_write(self, addr, vals):
        """
        Set Start Address (R0,R1) and consecutively write to R3.
        Each op involving R3 increments R0 automatically at the end.
        There is max. ~20 consecutive regs for one burst and no wrapping between R0 and R1.
        """
        if addr[0] != self.prev_addr[0]: self.transport.write(self.address,     addr[0])
        if addr[1] != self.prev_addr[1]: self.transport.write(self.address + 1, addr[1])
        for idx, val in enumerate(vals):
            self.transport.write(self.address + 3, val)
        # self.transport.write_regs(address=self.address + 3, reg_address_width=1, reg_address=vals[0], vals=vals[1:]) #to be tried, vals[0] used as reg_address; vals[0] and vals[1:] will be put back together in lpgbt.i2c_master_write function
        self.prev_addr = (addr[0]+len(vals),addr[1]) #adjust prev_addr to new R0 value
    
    def __read(self,sortedpairs):
        ret_pairs = {}
        for subList in sortedpairs:
            addr = list(subList[0].keys())[0]
            if len(subList) > 1:        # burst-read for grouped sortedpairs
                vals = self.__burst_read(addr,len(subList))
                for pair, val in zip(subList, vals):
                    addr = list(pair.keys())[0]
                    ret_pairs[addr] = val
            else:
                ret_pairs[addr] = self.__single_read(addr)
        return ret_pairs

    def __burst_read(self,addr,read_len):
        """ Set start reg address (R0,R1) and consecutively read from R3. """
        if addr[0] != self.prev_addr[0]: self.transport.write(self.address    , addr[0])
        if addr[1] != self.prev_addr[1]: self.transport.write(self.address + 1, addr[1])
        vals = []
        for idx in range(read_len):
            val = self.transport.read(self.address + 3)
            vals.append(val)
        self.prev_addr = (addr[0]+read_len,addr[1]) #adjust prev_addr to new R0 value
        return vals

    def __single_read(self,addr):
        """ Set reg address (R0,R1) and then read reg value (from R2). """
        if addr[0] != self.prev_addr[0]: self.transport.write(self.address    , addr[0])
        if addr[1] != self.prev_addr[1]: self.transport.write(self.address + 1, addr[1])
        val = self.transport.read(self.address + 2)
        self.prev_addr = addr
        return val

class dummyTransport(Transport):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        self.nwrite=0
        self.nread=0
        self.fout = open('output.txt','w')
        pass
    
    def write(self,address,val):
        self.nwrite+=1
        self.fout.write(f'writing addr,val : {address},{val}\n') 

    def read(self,address):
        self.nread+=1
        self.fout.write(f'reading addr : {address}\n') 
        return 0xca


def main():
    tr  = dummyTransport(name='i2c_w0',cfg={})
    rocs={}
    rocs['roc_s0'] = roc(name = 'roc_s0', cfg={'address':0x08,'init_config': 'configs/init_roc.yaml'})
    rocs['roc_s1'] = roc(name = 'roc_s1', cfg={'address':0x18})

    # with open('configs/init_roc.yaml') as fin:
    #     roc_config=yaml.safe_load(fin)['roc_s0']
    
    reset = lambda roc : roc.reset()
    roc_pattern = re.compile( '.*roc_.*' ) #look for *rocYXZ_* pattern (XYZ being digits)
    [ reset(rocs[key]) for key in rocs if roc_pattern.match(key)]

    [ rocs[key].set_transport(tr) for key in rocs if roc_pattern.match(key)]
    [ rocs[key].configure(rocs[key].init_config,read_back=False) for key in rocs if roc_pattern.match(key)]

    print(tr.nread,tr.nwrite)

    fillOutput = lambda outDict, roc : outDict[roc.name].update(roc.read(roc.init_config,from_cache=True))
    out_config = { 'rocs': { key:{} for key in rocs.keys() if roc_pattern.match(key)} }
    [ fillOutput(out_config['rocs'],rocs[key]) for key in rocs if roc_pattern.match(key)]
    print( yaml.dump(out_config) )


    with open('configs/small_config.yaml') as fin:
        roc_config=yaml.safe_load(fin)
    [ rocs[key].configure(roc_config,read_back=False) for key in rocs if roc_pattern.match(key)]
        
    fillOutput = lambda outDict, roc : outDict[roc.name].update(roc.read(roc_config,from_cache=True))
    out_config = { 'rocs': { key:{} for key in rocs.keys() if roc_pattern.match(key)} }
    [ fillOutput(out_config['rocs'],rocs[key]) for key in rocs if roc_pattern.match(key)]
    print( yaml.dump(out_config) )

    
if __name__ == '__main__':
    main()
