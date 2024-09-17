from swamp.core import Chip
import logging
import math
from swamp import lpgbt_adc

class vtrx(Chip):
    def __init__(self, name : str="", cfg : dict={}):
        super().__init__(name,cfg)
        self.address=cfg['address']

    def set_address(self,address):
        self.address=address

    def configure(self, cfg: dict, read_back: bool=False):
        self.logger.debug('in vtrx.configure')
        for reg,val in cfg.items():
            vals = [val]
            self.logger.info(f'calling transport.write_regs({self.address}, {0x1}, {reg}, {vals})')
            self.transport.write_regs(address=self.address, reg_address_width=0x1, reg_address=reg, reg_vals=vals)
        self.logger.debug('vtrx.configure done')

    def read(self, cfg: dict={}, from_cache: bool=False):
        self.logger.info(f'read with config = {cfg}')
        out_cfg={}
        for reg,_ in cfg.items():
            read_len=0x1
            self.logger.info(f'calling transport.read_regs({self.address}, {0x1}, {reg}, {read_len})')
            vals = self.transport.read_regs(address=self.address, reg_address_width=0x1, reg_address=reg, read_len=read_len)
            out_cfg[reg]=vals
        self.logger.debug(f'vtrx.read done; out config = {out_cfg}')
        return out_cfg

    def setup_temperature_read(self, adc_channel: lpgbt_adc.lpgbt_adc_channel, current_code: int = 127) -> None:
        '''
        Setup VTRx+ for temperature readout

        Arguments:
            adc_channel: ADC channel object
            current_code: current code to set the DAC to
        '''
        self.adc_channel = adc_channel
        self.adc_channel.current_dac_setup(current_code)

    def read_temperature(self) -> float:
        '''
        Read the VTRx+ temperature

        Returns:
            temperature: temperature in degrees Celsius
        '''
        voltage = self.adc_channel.read_voltage()
        resistance = voltage / 0.00045 # 450uA
        temperature = round((298.15 * 3500)/(298.15 * math.log(resistance/1000)+3500) - 273.15, 1)
        return temperature

