from typing import Literal
from time import sleep

from swamp.core import Chip
from swamp.gbtsca_gpio import gbtsca_gpio_pin, GBTSCA_GPIO_PIN_MAP
from swamp.gbtsca_analog import gbtsca_dac_channel, gbtsca_adc_channel, GBTSCA_ADC_PIN_MAP, GBTSCA_DAC_PIN_MAP
from swamp.gbtsca_i2c import gbtsca_i2c

class gbtsca(Chip):
    """
    SWAMP implementation of the GBT-SCA chip.

    Attributes:
        gpio_pins (list): List of gpio pins of the SCA. Only available if GPIOs
            have been enabled.
        dac_pins (list): List of DAC pins of the SCA. Only available if DAC
            functions have been enabled.
        adc_pins (list): List of ADC pins of the SCA. Only available if ADC
            functions have been enabled.
        adc_active (gbtsca_adc_channel): pointer to the currently active ADC channel.
        i2c_masters (list): List if I2C masters. Only available once I2C
            functions have been enabled.
    """

    def __init__(self, board_type: Literal['A', 'B', 'D', 'E', 'G', 'J', 'K'],
                 name : str="", cfg : dict={}):
        """
        Args:
            board_type (int): number of ROC controlled by this gbtsca
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary
        """
        super().__init__(name, cfg)
        self.gpio_pins = []
        self.dac_pins = []
        self.adc_pins = []
        self.adc_active = None
        self.i2c_masters = []
        self.board_type = board_type

    def enableGPIO(self):
        """
        Enable the GPIO block of the SCA and initialize the GPIO pins on the
        software side.

        Don't call this function twice!
        """
        self.transport.modifyControlRegister(0x00, 0x02, 1, 0x04000000, enable=True)
        self.gpio_pins = []
        for pin in range(32):
            cfg = {'pin': pin}
            p = gbtsca_gpio_pin("{}.gpio.{}".format(self.name, pin), cfg)
            p.set_carrier(self)
            self.gpio_pins.append(p)

    def disableGPIO(self):
        """
        Disable the GPIO block of the SCA, and remove the GPIO pin objects.
        """
        self.transport.modifyControlRegister(0x00, 0x02, 1, 0x04000000, enable=False)
        self.gpio_pins = []

    def getGPIO(self, pin):
        """
        Get the GPIO object for a specific pin.

        Args:
            pin: int or string
                The GPIO pin number or name.

        Returns:
            An instance of gbtsca_gpio_pin
        """
        if type(pin) is not int:
            # If string, translate to pin number.
            if not pin in GBTSCA_GPIO_PIN_MAP:
                raise ValueError(f"GPIO pin '{pin}' not defined in 'GBTSCA_GPIO_PIN_MAP'.")
            pin = GBTSCA_GPIO_PIN_MAP[pin]
        return self.gpio_pins[pin]

    def _setGPIODirections(self):
        """
        Set all GPIO pins direction.
        gbtsca.enableGPIO() must have been called.
        """
        if len(self.gpio_pins) != 32:
            raise ValueError(
                f"Found {len(self.gpio_pins)} GPIO pins while 32 are expected. "
                "Make sure gbtsca.enableGPIO() was called before this function."
            )

        self.getGPIO("PLL_LCK").set_dir(0)
        self.getGPIO("ERROR").set_dir(0)
        self.getGPIO("SOFT_RSTB").set_dir(1)
        self.getGPIO("I2C_RSTB").set_dir(1)
        self.getGPIO("HARD_RSTB").set_dir(1)
        self.getGPIO("PLL_LCK_2nd_ROC").set_dir(0)
        self.getGPIO("ERROR_2nd_ROC").set_dir(0)
        self.getGPIO("LED_ON_OFF").set_dir(1)
        self.getGPIO("LED_DISABLE1").set_dir(1)
        self.getGPIO("LED_DISABLE2").set_dir(1)
        self.getGPIO("LED_DISABLE3").set_dir(1)
        self.getGPIO("LED_DISABLE4").set_dir(1)
        self.getGPIO("LED_DISABLE5").set_dir(1)
        self.getGPIO("LED_DISABLE6").set_dir(1)
        self.getGPIO("LED_DISABLE7").set_dir(1)
        self.getGPIO("LED_DISABLE8").set_dir(1)
        self.getGPIO("LED_DISABLE1_2nd_ROC").set_dir(1)
        self.getGPIO("LED_DISABLE2_2nd_ROC").set_dir(1)
        self.getGPIO("ENHV0_2nd_Aldo").set_dir(1)
        self.getGPIO("ENHV1_2nd_Aldo").set_dir(1)
        self.getGPIO("ENHV0_Aldo").set_dir(1)
        self.getGPIO("ENHV1_Aldo").set_dir(1)
        self.getGPIO("LDO_ENABLE").set_dir(1)
        self.getGPIO("LDO_SOFTST").set_dir(1)
        self.getGPIO("M50MV_VDDD").set_dir(1)
        self.getGPIO("P50MV_VDDD").set_dir(1)
        self.getGPIO("M50MV_VDDA").set_dir(1)
        self.getGPIO("P50MV_VDDA").set_dir(1)
        self.getGPIO("PG_LDO").set_dir(0)
        self.getGPIO("OCZ_LDO").set_dir(0)
        self.getGPIO("LED_DISABLE3_2nd_ROC").set_dir(0)
        self.getGPIO("LED_DISABLE4_2nd_ROC").set_dir(0)

    def reset(self, mode: Literal["SOFT", "I2C", "HARD"] = "HARD"):
        """
        Send a reset command.

        Args:
            mode: str = SOFT | I2C | HARD
                GPIO reset pin to act on.
        """
        pin = self.getGPIO(f"{mode}_RSTB")
        pin.up()
        pin.down()
        pin.up()

    def startupGPIO(self):
        """
        Startup the communication lines.
        GPIO directions must have been set beforehand.
        """
        self._setGPIODirections()
        sleep(1)
        self.getGPIO("LDO_SOFTST").up()
        self.getGPIO("LDO_ENABLE").up()
        sleep(1)
        # self.reset("SOFT")
        # self.reset("I2C")
        self.reset("HARD")
        sleep(1)

    def printGPIOStatus(self):
        """
        Reads and prints the status of all GPIO pins.
        """
        self.transport.clearCommands()
        self.transport.addCommand(0x02, 0x21) # read GPIO direction
        self.transport.addCommand(0x02, 0x11) # read DATAOUT
        self.transport.addCommand(0x02, 0x01) # read DATAIN
        dirs, douts, dins = self.transport.dispatchCommands()
        for name, pin in GBTSCA_GPIO_PIN_MAP.items():
            dir = (dirs["payload"] & (1 << pin)) >> pin
            din = (dins["payload"] & (1 << pin)) >> pin
            dout = (douts["payload"] & (1 << pin)) >> pin
            self.logger.info("GPIO %02d: %s,  %d  (%s)",
                pin,
                " IN" if dir == 0 else "OUT",
                din if dir == 0 else dout,
                name)

    def enableDAC(self):
        """
        Enable the DAC block of the SCA and initialize the list of DAC pins.

        Don't call this function twice!

        TODO Not tested for GBT-SCA v1
        """
        # TODO According to the GBT-SCA manual, the data should be 0x40000000 instead of 0x20000000
        # Maybe this is due to the SCA version 1?
        self.transport.modifyControlRegister(0x00, 0x06, 1, 0x20000000, enable=True)
        self.dac_pins = []
        for pin in range(4):
            cfg = {'pin': pin}
            p = gbtsca_dac_channel("{}.dac.{}".format(self.name, pin), cfg)
            p.set_carrier(self)
            self.dac_pins.append(p)

    def disableDAC(self):
        """
        Disable the DAC block and remove the DAC pin objects.

        TODO Not tested for GBT-SCA v1
        """
        self.transport.modifyControlRegister(0x00, 0x06, 1, 0x20000000, enable=False)
        self.dac_pins = []

    def getDAC(self, pin):
        """
        Args:
            pin: int or str
                The pin number or name of the DAC to get.

        Returns:
            An instance of gbtsca_dac_channel
        """
        if type(pin) is not int:
            # If string, translate to pin number.
            if not pin in GBTSCA_DAC_PIN_MAP:
                raise ValueError(f"DAC pin '{pin}' not defined in 'GBTSCA_DAC_PIN_MAP'.")
            pin = GBTSCA_DAC_PIN_MAP[pin]
        return self.dac_pins[pin]

    def printDACs(self):
        """
        Print all DAC values.
        """
        self.logger.info("======== DAC values ========")
        for name in ("REF_HV0_21k", "REF_HV0_100k", "REF_HV1_21k", "REF_HV1_100k"):
            self.logger.info(
                "%12s: %3d = %.3f",
                name,
                self.getDAC(name).read_value(),
                self.getDAC(name).get_voltage()
            )

    def enableADC(self):
        """
        Enable the ADC block of the SCA and initialize the list of ADC pins.

        """
        self.transport.modifyControlRegister(0x00, 0x06, 1, 0x10000000, enable=True)
        self.adc_pins=[]
        for pin in range(32):
            cfg = {'pin': pin}
            p = gbtsca_adc_channel("{}.adc.{}".format(self.name, pin), cfg)
            p.set_carrier(self)
            self.adc_pins.append(p)

    def disableADC(self):
        """
        Disable the ADC block and remove the DAC pin objects.
        """
        self.transport.modifyControlRegister(0x00, 0x06, 1, 0x10000000, enable=False)
        self.adc_pins = []
        self.adc_active = None

    def getSerialNumber(self):
        """
        Read the serial number.  NB: the ADC block must be enabled, which we will do.
        """
        self.transport.modifyControlRegister(0x00, 0x06, 1, 0x10000000)
        self.transport.addCommand(0x14, 0xD1, 1, 1)
        sn = self.transport.dispatchCommands()
        return sn[0]['payload']

    def getADC(self, pin):
        """
        Args:
            pin: int or str
                The pin number or the name of the ADC to get.

        Returns:
            An instance of gbtsca_adc_channel
        """
        if type(pin) is not int:
            # If string, translate to pin number.
            if not pin in GBTSCA_ADC_PIN_MAP[self.board_type]:
                raise ValueError(
                    f"ADC pin '{pin}' not defined in "
                    f"'GBTSCA_ADC_PIN_MAP[{self.board_type}]'."
                )
            pin = GBTSCA_ADC_PIN_MAP[self.board_type][pin]
        return self.adc_pins[pin]

    def printTemperatures(self):
        """
        Print all temperatures read from the ADCs.
        """
        self.logger.info("======== ADC status - temperature ========")
        for name in (f"PT1000_T{i}" for i in range(1, 9)):
            # Up to 8 temperature probes connected [1, 9], but not all on B/J/K boards.
            if not name in GBTSCA_ADC_PIN_MAP[self.board_type]:
                self.logger.debug(
                    "ADC pin '%s' not found in pin map (board_type = %d)",
                    name,
                    self.board_type
                )
                continue
            self.logger.info(
                "%s: %.1f C (%d)",
                name,
                self.getADC(name).read_temperature(method='PT1000'),
                self.getADC(name).read_value()
            )

    def printVoltages(self):
        """
        Print all voltages read fom the ADCs.
        """
        self.logger.info("======== ADC status - voltage ========")
        for name in (
            "VCC_GBTSCA", "VCC_IN", "VPA", "PRE_VPA", "VDDA", "VDDD", "PRE_VDDA",
            "MPPC_BIAS_IN", "MPPC_BIAS1", "MPPC_BIAS2",
            "MPPC_BIAS3", "MPPC_BIAS4",  # B,J,K
            "PROBE_DC_L1", "PROBE_PA_L", "PROBE_DC_R1", "PROBE_PA_R",
            "PROBE_PA2_R", "PROBE_PA2_R_2nd_ROC",  # B,J,K
            "PROBE_DC_L1_2nd_ROC", "PROBE_PA2_L",  # J,K
            "CURHV0", "CURHV1",
            "CURHV1_ALDO2", "CURHV0_ALDO2",  # B,J,K
        ):
            if not name in GBTSCA_ADC_PIN_MAP[self.board_type]:
                # Some value are not available in all versions.
                self.logger.debug(
                    "ADC pin '%s' not found in pin map (board_type = %d)",
                    name,
                    self.board_type
                )
                continue
            self.logger.info(
                "%s: %.3f V (%d)",
                name,
                self.getADC(name).read_voltage(),
                self.getADC(name).read_value()
            )

    def enableI2C(self):
        for pin in range(16):
            cfg = {'pin': pin}
            p = gbtsca_i2c("{}.i2c.{}".format(self.name, pin), cfg)
            p.set_carrier(self)
            self.i2c_masters.append(p)

    def disableI2C(self):
        """
        Enable the I2C block of the SCA and initialize the list of I2C masters.

        Don't call this function twice!

        TODO: not implemented
        """
        pass

    def getI2C(self, pin):
        """
        Args:
            pin (int): The index of the I2C master to get.

        Returns:
            An instance of gbtsca_i2c
        """
        return self.i2c_masters[pin]
