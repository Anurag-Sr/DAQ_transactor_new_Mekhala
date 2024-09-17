from lpgbt_control_lib import LpgbtV1
from swamp.core import Chip
import logging
import pickle
import yaml
import os
import swamp
from swamp import lpgbt_gpio, lpgbt_adc
from nested_dict import nested_dict
from pprint import pprint
from typing import Any, Dict

class sc_lpgbt(Chip):
    def __init__(self, name : str="", cfg : dict={}):
        super().__init__(name,cfg)
        self.address=cfg['address']
        self.lpgbt = LpgbtV1(logger=self.logger)
        self.config_cache = {}
        self.reset_pin = None
        self.transport = None

        self.regmapfile=os.path.join(swamp.base_path, './configs/lpgbt_map.pickle')
        if 'regmapfile' in cfg:
            self.regmapfile=cfg['regmapfile']
        try:
            with open(self.regmapfile,'rb') as fin:
                self.regmap = pickle.load(fin)
        except Exception as e:
            self.logger.critical(f'Error when trying to load the sc_lpgbt reg map : {self.regmapfile}')
            self.logger.critical(f'Exception : {str(e)}')
            self.logger.critical(f'The process will exit')
            exit(1)

        self.lpgbt.register_comm_intf(
            name="Mirror",
            write_regs=self.write_regs,
            read_regs=self.read_regs,
            default=True
        )
        # # register r/w pin interface
        # self.lpgbt.register_ctrl_pin_access(
        #     self._write_pin, # currently not implemented
        #     self._read_pin
        # )

    def set_address(self,address):
        self.address=address

    def init_gpio(self,gpio_dirs=[0 for i in range(16)] ):
        self.gpio_pins=[]
        for pin in range(16):
            pin_config={}
            pin_config['pin']=pin
            pin_name = self.name+'.gpio.'+str(pin)
            gpio_pin = lpgbt_gpio.lpgbt_gpio_pin(name=pin_name,cfg=pin_config)
            gpio_pin.set_carrier(self)
            if self.transport is not None:
                gpio_pin.set_dir(gpio_dirs[pin])
            self.gpio_pins.append(gpio_pin)
                
            
    def __chunkConfig__(self,cfg):
        address_and_vals={}
        prev_address = -1
        first_reg_addr = 0x0
        for reg,val in cfg.items():
            address=val['address']
            data=val['data']
            if address-prev_address==1 and prev_address>-1:
                address_and_vals[ first_reg_addr ].append(data)
            else:
                address_and_vals[address]=[data]
                first_reg_addr=address
            prev_address = address
        return address_and_vals

    def __from_cfg_to_reg_and_val__(self,cfg):
        self.logger.debug("\t in sc_lpbgt.__from_cfg_to_reg_and_val__")
        lpgbt_cfg = nested_dict()
        for key,val in cfg.items():
            try:
                address = int(key, 0)
            except ValueError:
                address = int(self.regmap[key]['address'],16)
            lpgbt_cfg[key] = { 'data' : val , 'address' : address }
                
        lpgbt_cfg = nested_dict({k: v for k, v in sorted(lpgbt_cfg.items(), key=lambda item: item[1]['address'])})
        return self.__chunkConfig__(lpgbt_cfg)

    def __from_reg_and_val_to_cfg__(self,reg_and_vals):
        self.logger.debug("\t in sc_lpbgt.__from_reg_and_val_to_cfg_")
        reg = reg_and_vals[0]
        vals = reg_and_vals[1]

        cfg = {}
        for v in vals:
            key = next((key for key,item in self.regmap.items() if item['address'] == f'0x{reg:04x}'), None)
            cfg[key]=v
            reg+=1
        return cfg
    
    def configure(self, cfg: dict, read_back: bool=False):
        self.logger.debug("in sc_lpgbt.configuration")
        regs_and_vals = self.__from_cfg_to_reg_and_val__(cfg)
        for reg_addr,vals in regs_and_vals.items():
            self.logger.debug(f'1st reg address to write = {reg_addr}, payload = {vals}')
            self.write_regs(reg_addr,vals)
        self.logger.debug("sc_lpgbt.configuration done")

    def read(self, cfg: dict={}, from_cache: bool=False):
        self.logger.debug(f'read with config = {cfg}')
        regs_and_vals = self.__from_cfg_to_reg_and_val__(cfg)
        ret={}
        for reg_addr,reg_vals in regs_and_vals.items():
            self.logger.debug(f'1st reg address to read = {reg_addr}, reading {len(reg_vals)} bytes')
            vals = self.read_regs(reg_addr,len(reg_vals))
            response = self.__from_reg_and_val_to_cfg__( (reg_addr,vals) )
            self.logger.debug(f'response = {response}')
            ret.update(response)
        self.logger.debug("sc_lpgbt.read done")
        return ret
        
    def get_gpio_pin(self,pin):
        return self.gpio_pins[pin]

    def log_gpio_status(self):
        self.lpgbt.log_gpio()

    def write_regs(self,reg_addr,reg_vals):
        self.logger.debug("in lpgbt.write_regs")
        self.transport.write_regs(address=self.address, reg_address_width=0x2, reg_address=reg_addr, reg_vals=reg_vals)
        self.logger.debug("lpgbt.write_regs done")

    def write_reg(self,reg_addr,val):
        reg_vals = [val]
        self.write_regs(reg_addr,reg_vals)

    def read_regs(self,reg_addr,read_len):
        self.logger.debug("in lpgbt.read_reg")
        reg_vals = self.transport.read_regs(address=self.address, reg_address_width=0x2, reg_address=reg_addr, read_len=read_len)
        self.logger.debug("lpgbt.read_reg done")
        return reg_vals

    def read_reg(self,reg_addr):
        read_len=1
        return self.read_regs(reg_addr,read_len)

    def dump(self,outfile):
        self.logger.debug("in sc_lpgbt.dump")
        nreg=0x200
        reg_addr = 0x0
        reg_vals = self.read_regs(reg_addr=reg_addr,read_len=nreg)
        config = {}
        for reg, val in enumerate(reg_vals):
            if val == 0:
                continue
            config.update(self.__from_reg_and_val_to_cfg__([reg, [val]]))
        # regs_and_vals = ([str(reg) for reg in range(nreg)],[hex(v) for v in reg_vals])
        # regs_and_vals = dict(zip([reg for reg in range(nreg)],zip([hex(reg) for reg in range(nreg)],reg_vals)))
        # if outfile :
        if os.path.splitext(outfile)[1]=='':
            outfile=outfile+'.yaml'
        elif os.path.splitext(outfile)[1]!='yaml':
            self.logger.warning(f'sc_lpgbt dump was called with outfile = {outfile}. It does not have .yaml extension and yaml format will be used anyway!!')
        self.logger.debug(f'sc_lpgbt dump in {outfile}')
        with open(outfile,'w') as fout:
            yaml.dump(config, fout, sort_keys=False)
        # else:
        #     pprint( regs_and_vals )

    def init_adc_channels(self, cfg: Dict[str, Dict[str, Any]], vref: int = 140) -> None:
        '''
        Setup the ADC channels
        
        Arguments:
            cfg {dict}: dictionary with the configuration of the ADC channels
            vref: Sets the vref tune code. Default is 140.

        '''
        self.adc_channels = {}
        self.lpgbt.vref_enable(True, vref)
        for key, item in cfg.items():
            adc_name = f'{self.name}:{key}'
            cfg_ch = {
                'lpgbt': self.lpgbt,
                'channel_p': item['channel_p'],
                'channel_n': item.get('channel_n', self.lpgbt.AdcInputSelect.VREF2),
            }
            self.adc_channels[key] = lpgbt_adc.lpgbt_adc_channel(key,cfg_ch)
    
    def get_adc_channel(self, name: str) -> lpgbt_adc.lpgbt_adc_channel:
        '''
        Get a specific adc_channel

        Arguments:
            name {str}: name of the ADC channel

        Returns:
            ADC channel object
        '''
        return self.adc_channels[name]
    
    def read_temperature(self) -> float:
        '''
        Read the temperature of the lpGBT

        Returns:
            Temperature in degrees Celsius
        '''
        reading = self.adc_channels['internal_temperature'].read()
        temperature = round((reading - 486.2)/2.105, 1)
        return temperature

            
def main():
    lpgbt = sc_lpgbt(name = 'dummy', cfg={'address':0x70})
    reg_and_vals = (200,[[2,23,23,12]])
    print(lpgbt.__from_reg_and_val_to_cfg__(reg_and_vals))

if __name__ == '__main__':
    main()
