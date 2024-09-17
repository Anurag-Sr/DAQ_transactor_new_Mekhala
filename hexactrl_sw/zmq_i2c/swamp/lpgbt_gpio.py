from swamp.core import GPIO
import logging
import swamp.util as util

class lpgbt_gpio_pin(GPIO):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        try:
            self.pin = cfg['pin']
            self.logger.info(f'creating an instance of {self.name}')
            dir_map = {'input' : 0, 'output': 1}
            self.direction = dir_map[ cfg['dir'] ] if 'dir' in cfg else 1
        except:
            self.logger.critical(f'Wrong configuration format when creating {self.name}')
            self.logger.critical(f'Configuration used : {cfg}')
            self.logger.critical(f'Proper configuration needs "pin" keys;')
            self.logger.critical(f'exit')
            exit(1)

        assert self.pin in range(16)
        self.cache = {}
        
    def set_carrier(self,carrier):
        self.lpgbt=carrier

    def set_dir(self,dir:int=-1):
        if dir>=0:
            direction = dir
        else:
            direction = self.direction

        self.lpgbt.lpgbt.gpio_set_dir_bit(self.pin,direction)
        self.logger.info(f' Set dir of GPIO pin {self.pin} as {direction}')
        self.cache['dir'] = direction

    def get_dir(self,from_cache=False):
        if 'dir' not in self.cache or from_cache==False:
            self.cache['dir'] = self.lpgbt.lpgbt.gpio_get_dir_bit(self.pin)
        return self.cache['dir']

    def set_drive(self, drive_strength):
        self.lpgbt.lpgbt.gpio_set_drive_bit(bit=self.pin,drive_strength=drive_strength)

    def get_drive(self):
        self.lpgbt.lpgbt.gpio_get_drive_bit(bit=self.pin)

    def up(self):
        self.lpgbt.lpgbt.gpio_set_out_bit(self.pin,0x1)
        self.cache['status'] = 1

    def down(self):
        self.lpgbt.lpgbt.gpio_set_out_bit(self.pin,0x0)
        self.cache['status'] = 0

    def is_up(self,from_cache=False):
        if 'status' not in self.cache or from_cache==False:
            self.cache['status'] = self.lpgbt.lpgbt.gpio_get_out_bit(self.pin)
        return self.cache['status']==0x1

    def is_down(self,from_cache=False):
        if 'status' not in self.cache or from_cache==False:
            self.cache['status'] = self.lpgbt.lpgbt.gpio_get_out_bit(self.pin)
        return self.cache['status']==0x0

    def status(self,from_cache=False):
        if 'status' not in self.cache or from_cache==False:
            self.cache['status'] = self.lpgbt.lpgbt.gpio_get_out_bit(self.pin)
        return self.cache['status']


class lpgbt_gpio_reset_pin(lpgbt_gpio_pin):
    def register_chip(self,chip):
        self.chips.append(chip)
        chip.set_reset_pin(self)
