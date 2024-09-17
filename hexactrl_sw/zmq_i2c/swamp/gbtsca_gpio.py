from swamp.core import GPIO

GBTSCA_GPIO_PIN_MAP = {
    'PLL_LCK'               : 0,
    'ERROR'                 : 1,
    'SOFT_RSTB'             : 2,
    'I2C_RSTB'              : 3,
    'HARD_RSTB'             : 4,
    'PLL_LCK_2nd_ROC'       : 5,
    'ERROR_2nd_ROC'         : 6,
    'LED_ON_OFF'            : 7,
    'LED_DISABLE1'          : 8,
    'LED_DISABLE2'          : 9,
    'LED_DISABLE3'          : 10,
    'LED_DISABLE4'          : 11,
    'LED_DISABLE5'          : 12,
    'LED_DISABLE6'          : 13,
    'LED_DISABLE7'          : 14,
    'LED_DISABLE8'          : 15,
    'LED_DISABLE1_2nd_ROC'  : 16,
    'LED_DISABLE2_2nd_ROC'  : 17,
    'ENHV0_2nd_Aldo'        : 18,
    'ENHV1_2nd_Aldo'        : 19,
    'ENHV0_Aldo'            : 20,
    'ENHV1_Aldo'            : 21,
    'LDO_ENABLE'            : 22,
    'LDO_SOFTST'            : 23,
    'M50MV_VDDD'            : 24,
    'P50MV_VDDD'            : 25,
    'M50MV_VDDA'            : 26,
    'P50MV_VDDA'            : 27,
    'PG_LDO'                : 28,
    'OCZ_LDO'               : 29,
    'LED_DISABLE3_2nd_ROC'  : 30,
    'LED_DISABLE4_2nd_ROC'  : 31,
}


class gbtsca_gpio_pin(GPIO):
    """
    This class represents one GPIO pin of the GBT-SCA.

    Attributes:
        pin (int): The index of the pin that this object represents.
        cache (dict): Cache to store GPIO properties.
        sca (gbtsca): Chip that carries this GPIO.
    """

    def __init__(self, name : str="", cfg : dict={} ):
        """
        Args:
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary

        Configuration parameters:
            pin (int): The index of the pin that this object represents.
            dir (int): Direction of the GPIO pin. 0 = input, 1 = output.
                Defaults to 0 = input.

        Raises:
            AssertionError: if pin index is < 0 or > 31.
        """
        super().__init__(name,cfg)
        try:
            self.pin = cfg['pin']
            self.logger.info(f'creating an instance of {self.name}')
            dir_map = {'input' : 0, 'output': 1}
            self.direction = dir_map[ cfg['dir'] ] if 'dir' in cfg else 0
        except:
            self.logger.critical(f'Wrong configuration format when creating {self.name}')
            self.logger.critical(f'Configuration used : {cfg}')
            self.logger.critical(f'Proper configuration needs "pin" keys;')
            self.logger.critical(f'exit')
            exit(1)

        assert self.pin in range(32)
        self.cache = {}

    def set_carrier(self, carrier):
        """
        Args:
            carrier (gbtsca): Must be an instance of the GBT-SCA chip class.
        """
        self.sca = carrier

    def set_dir(self, dir:int=-1):
        """
        Set the direction of the GPIO pin.

        Args:
            dir (int): 0 -> input, 1 -> output
        """
        if dir>=0:
            direction = dir
        else:
            direction = self.direction

        mask = 1 << self.pin
        self.sca.transport.modifyControlRegister(0x02, 0x20, 4, mask, enable=(dir==1))
        self.logger.info(f' Set dir of GPIO pin {self.pin} as {direction}')
        self.cache['dir'] = direction

    def get_dir(self, from_cache=False):
        """
        Get the direction of the pin:

        Args:
            from_cache (bool): If true, the property will not be read from the
                SCA, but just from the cache of this GPIO object. This option
                can be used to reduce the communication to the front end.
                Default is false.

        Returns:
            int: 0 -> input, 1 -> output
        """
        if 'dir' not in self.cache or from_cache==False:
            self.sca.transport.clearCommands()
            self.sca.transport.addCommand(0x02, 0x21, 1, 0x00)
            gpio_data = self.sca.transport.dispatchCommands()
            self.logger.debug(f'GPIO data {gpio_data}')
            # dispatchCommands returns a list of dictionaries,
            # each dictionary corresponding to the output of one command.
            # Since we only pass one command here (ensured by calling
            # clearCommands() first), we need to retrieve the payload of
            # that one response.
            self.cache['dir'] = ((gpio_data[0]['payload'] & (1 << self.pin)) >> self.pin)
        return self.cache['dir']

    def up(self):
        """
        Set the pin to logical high (1)
        """
        mask = 1 << self.pin
        self.sca.transport.modifyControlRegister(0x02, 0x10, 4, mask, enable=True)
        self.cache['status'] = 1

    def down(self):
        """
        Set the pin to logical low (0)
        """
        mask = 1 << self.pin
        self.sca.transport.modifyControlRegister(0x02, 0x10, 4, mask, enable=False)
        self.cache['status'] = 0

    def __read_status(self):
        """
        Reads the status of the GPIO pin and stores it in the interal cache of
        this object.
        """
        self.sca.transport.clearCommands()
        self.sca.transport.addCommand(0x02, 0x01, 1, 0x00)
        gpio_data = self.sca.transport.dispatchCommands()[0]['payload']
        self.cache['status'] = ((gpio_data & (1 << self.pin)) >> self.pin)

    def is_up(self, from_cache=False):
        """
        Args:
            from_cache (bool): If true, the property will not be read from the
                SCA, but just from the cache of this GPIO object. This option
                can be used to reduce the communication to the front end.
                Default is false.

        Returns:
            bool: True if pin is high, else False
        """
        if 'status' not in self.cache or from_cache==False:
            self.__read_status()
        return self.cache['status']==0x1

    def is_down(self, from_cache=False):
        """
        Args:
            from_cache (bool): If true, the property will not be read from the
                SCA, but just from the cache of this GPIO object. This option
                can be used to reduce the communication to the front end.
                Default is false.

        Returns:
            bool: False if pin is high, else True
        """
        if 'status' not in self.cache or from_cache==False:
            self.__read_status()
        return self.cache['status']==0x0

    def status(self, from_cache=False):
        """
        Args:
            from_cache (bool): If true, the property will not be read from the
                SCA, but just from the cache of this GPIO object. This option
                can be used to reduce the communication to the front end.
                Default is false.

        Returns:
            int: Pin status: 1 -> high, 0 -> low
        """
        if 'status' not in self.cache or from_cache==False:
            self.__read_status()
        return self.cache['status']
