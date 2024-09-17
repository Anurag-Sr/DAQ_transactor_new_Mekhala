import swamp.util as util
import swamp.lpgbt_adc as lpgbt_adc

from typing import Union

class pt1000:
    def __init__(self, adc_channel: lpgbt_adc.lpgbt_adc_channel, current_code: int = 127):
        '''
        PT1000 class on hexaboard

        Arguments:
            adc_channel: ADC channel object
            current_code: current code to set the DAC to
        '''
        self.logger = util.getLogger(f'pt1000.{adc_channel.name}')
        self.adc_channel = adc_channel
        self.adc_channel.current_dac_setup(current_code)
        self.logger.info(f'creating an instance of {self.logger.name}')
    
    def read_temperature(self, n_samples: int = 1) -> Union[float, list]:
        '''
        Read the temperature of the hexaboard pt1000
        
        Returns:
            Temperature in degrees Celsius
        '''
        voltage = self.adc_channel.read_voltage(n_samples)
        if isinstance(voltage, list):
            return [self.__voltage_to_temperature(v) for v in voltage]
        return self.__voltage_to_temperature(voltage)
    
    def __voltage_to_temperature(self, voltage: float) -> float:
        '''
        Converts voltage to temperature
        
        Arguments:
            voltage: voltage to convert
        
        Returns:
            Temperature in degrees Celsius
        '''
        resistance = voltage / 0.00045
        temperature = round((resistance-1000)/(1000*0.00391), 1)
        return temperature
