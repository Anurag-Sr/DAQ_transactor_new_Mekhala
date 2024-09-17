from swamp.core import SwampObject

GBTSCA_DAC_PIN_MAP = {
    "REF_HV0_21k":  0,
    "REF_HV0_100k": 1,
    "REF_HV1_21k":  2,
    "REF_HV1_100k": 3,
}


# The ADC pinout is slightly different A/D/E/G, B, J/K versions of the boards.
# D, B and J are defined, the other keys are added as copies of these
# ones at the end of the dictionary definition such that all of A/B/D/E/G/J/K
# are available keys in this dictionary.
GBTSCA_ADC_PIN_MAP = {
    'D': {  # A/D/E/G boards
        "PT1000_T2":            0,
        "PT1000_T4":            1,
        "PT1000_T1":            2,
        "PT1000_T6":            3,
        "PT1000_T3":            4,
        "PT1000_T8":            5,
        "PT1000_T7":            6,
        "PT1000_T5":            7,
        "VCC_GBTSCA":           8,
        "MPPC_BIAS1":           9,
        "MPPC_BIAS2":           10,
        "VCC_IN":               11,
        "LED_BIAS":             12,
        "VPA":                  13,
        "PRE_VPA":              14,
        "VDDA":                 15,
        "VDDD":                 16,
        "PRE_VDDA":             17,
        "MPPC_BIAS_IN":         18,
        # no pin 19
        # no pin 20
        # no pin 21
        "PROBE_DC_L1":          22,
        "PROBE_PA_L":           23,
        "PROBE_DC_R1":          24,
        "PROBE_PA_R":           25,
        "BOARD_ID_0":           26,
        "BOARD_ID_1":           27,
        # no pin 28
        "CURHV0":               29,
        "CURHV1":               30,
        # no pin 31
    },
    'B': {
        "PT1000_T2":            0,
        "PT1000_T4":            1,
        "PT1000_T1":            2,
        "PROBE_PA2_R":          3,  # Changed for B.
        "PT1000_T3":            4,
        "PT1000_T8":            5,
        "PT1000_T7":            6,
        "PROBE_PA2_R_2nd_ROC":  7,  # Changed for B.
        "VCC_GBTSCA":           8,
        "MPPC_BIAS1":           9,
        "MPPC_BIAS2":           10,
        "VCC_IN":               11,
        "LED_BIAS":             12,
        "VPA":                  13,
        "PRE_VPA":              14,
        "VDDA":                 15,
        "VDDD":                 16,
        "PRE_VDDA":             17,
        "MPPC_BIAS_IN":         18,
        "MPPC_BIAS4":           19,  # Changed for B.
        "MPPC_BIAS3":           20,  # Changed for B.
        # no pin 21
        "PROBE_DC_L1":          22,
        "PROBE_PA_L":           23,
        "PROBE_DC_R1":          24,
        "PROBE_PA_R":           25,
        "BOARD_ID_0":           26,
        "CURHV1_ALDO2":         27,  # Changed for B.
        "CURHV0_ALDO2":         28,  # Changed for B.
        "CURHV0":               29,
        "CURHV1":               30,
        # no pin 31
    },
    'J': {  # J/K boards
        "PT1000_T2":            0,
        "PT1000_T4":            1,
        "PT1000_T1":            2,
        "PROBE_PA2_R":          3,  # Changed for B.
        "PROBE_DC_L1_2nd_ROC":  4,  # Changed for J/K.
        "PT1000_T8":            5,
        "PT1000_T7":            6,
        "PROBE_PA2_R_2nd_ROC":  7,  # Changed for B.
        "VCC_GBTSCA":           8,
        "MPPC_BIAS1":           9,
        "MPPC_BIAS2":           10,
        "VCC_IN":               11,
        "LED_BIAS":             12,
        "VPA":                  13,
        "PRE_VPA":              14,
        "VDDA":                 15,
        "VDDD":                 16,
        "PRE_VDDA":             17,
        "MPPC_BIAS_IN":         18,
        "MPPC_BIAS4":           19,  # Changed for B.
        "MPPC_BIAS3":           20,  # Changed for B.
        "PROBE_PA2_L":          21,  # Changed for J/K.
        "PROBE_DC_L1":          22,
        "PROBE_PA_L":           23,
        "PROBE_DC_R1":          24,
        "PROBE_PA_R":           25,
        "BOARD_ID_0":           26,
        "CURHV1_ALDO2":         27,  # Changed for B.
        "CURHV0_ALDO2":         28,  # Changed for B.
        "CURHV0":               29,
        "CURHV1":               30,
        # no pin 31
    },
}
# Add identical configurations (A,D,E,G / B / J,K).
GBTSCA_ADC_PIN_MAP['A'] = GBTSCA_ADC_PIN_MAP['D']
GBTSCA_ADC_PIN_MAP['E'] = GBTSCA_ADC_PIN_MAP['D']
GBTSCA_ADC_PIN_MAP['G'] = GBTSCA_ADC_PIN_MAP['D']
GBTSCA_ADC_PIN_MAP['K'] = GBTSCA_ADC_PIN_MAP['J']


class gbtsca_analog_channel(SwampObject):
    """
    Base class for ADC and DAC channels of the GBT-SCA.

    Attributes:
        pin (int): The index of the pin that this object represents.
        carrier (gbtsca): Chip that carries this GPIO.
    """

    def __init__(self, name : str="", cfg : dict={}):
        """
        Args:
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary

        Configuration parameters:
            pin (int): The index of the pin that this object represents.
        """
        super().__init__(name, cfg)
        self.pin = cfg["pin"]
        self.carrier = None

    def set_carrier(self, carrier):
        """
        Args:
            carrier (gbtsca): Must be an instance of the GBT-SCA chip class.
        """
        self.carrier = carrier


class gbtsca_adc_channel(gbtsca_analog_channel):
    """
    This calss represents an ADC channel of the GBT-SCA chip.
    """

    def __init__(self, name : str="", cfg : dict={}):
        """
        Args:
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary

        Configuration parameters:
            pin (int): The index of the pin that this object represents.

        Raises:
            AssertionError: if pin index is < 0 or > 31
        """
        super().__init__(name, cfg)
        assert self.pin >= 0 and self.pin < 32

    def activate(self):
        """
        Activate this ADC channel
        """
        self.carrier.transport.clearCommands()
        self.carrier.transport.addCommand(0x14, 0x50, 1, self.pin)
        self.carrier.transport.dispatchCommands()

        self.carrier.transport.addCommand(0x14, 0x51)
        self.carrier.transport.dispatchCommands()
        self.carrier.adc_active = self

    def __measureADCValue(self):
        """
        Returns:
            int: Measured ADC value of the currently selected channel.
        """
        # Send ADC_GO command to start the measurement
        self.carrier.transport.clearCommands()
        self.carrier.transport.addCommand(0x14, 0x02, 4, 0x00000001)
        self.carrier.transport.dispatchCommands()

        # Read the result: Command ADC_R_DATA
        self.carrier.transport.addCommand(0x14, 0x21)
        return self.carrier.transport.dispatchCommands()

    def read_value(self):
        """
        Activated this ADC channel if necessary, and measures the ADC value.

        Returns:
            int: Measured ADC value of the this channel.
        """
        if self.carrier.adc_active != self:
            self.activate()

        value = self.__measureADCValue()
        return value[0]['payload']

    def read_voltage(self, R1=None, R2=None):
        """
        Activated this ADC channel if necessary, and measures the ADC value.

        Params:
            R1, R2 (float): Values for the voltage divider. If R1 and R2 are
            None, then the measured voltage is returned directly. Otherwise,
            the returned voltage is V * (R1 + R2) / R2

        Returns:
            float: Measured ADC value in volts.
        """
        value = self.read_value()
        if R1 is not None and R2 is not None:
            value *= (R1 + R2) / R2
        return value / 4096

    def read_temperature(self, method="SCA"):
        """
        Activated this ADC channel if necessary, and measures the ADC value.

        Params:
            method (str): How to calculate the temperature value. Default is
                "SCA" meaning the internal temperature reference of the
                chip. Other option: "PT1000", meaning external sensor on the
                tileboard.

        Returns:
            float: Measured ADC value converted to degree Celsius.
        """
        voltage = self.read_voltage()
        if method == "PT1000":
            return voltage * 736.84 - 679.89
        else:
            return (voltage - 0.716) / (-1.829) * 1000


class gbtsca_dac_channel(gbtsca_analog_channel):
    """
    This calss represents an DAC channel of the GBT-SCA chip.

    TODO: not tested on GBT-SCA v1
    """

    def __init__(self, name : str="", cfg : dict={}):
        """
        Args:
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary

        Configuration parameters:
            pin (int): The index of the pin that this object represents.

        Raises:
            AssertionError: if pin index is < 0 or > 3
        """
        super().__init__(name, cfg)
        assert self.pin >= 0 and self.pin < 4

    def set_value(self, value):
        """
        Args:
            value (int): DAC value to set

        Raises:
            AssertionError: if value is not in 8bit range
        """
        assert value >= 0 and value < 256
        self.carrier.transport.clearCommands()
        self.carrier.transport.addCommand(0x15, 0x10*(self.pin+1), 1, value << 24)
        self.carrier.transport.dispatchCommands()

    def set_voltage(self, voltage, calibration=1.25):
        """
        Args:
            voltage (float): Voltage to set. If the ADC value would be below 0
                or above 255, it caps at that value. No assertion errors.
            calibration (float): Calibration factor for the DAC.
        """
        value = int(voltage * 255 / calibration)
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        self.set_value(value)

    def get_value(self):
        """
        Returns:
            int: the current set vale in DAC ticks (8 bit)
        """
        self.carrier.transport.clearCommands()
        self.carrier.transport.addCommand(0x15, 0x10 * (self.pin+1) + 1)
        reply = self.carrier.transport.dispatchCommands()
        return (reply[0]['payload'] >> 24) & 0xff

    def get_voltage(self, calibration=1.25):
        """
        Args:
            calibration (float): Calibration factor for the DAC.

        Returns:
            float: the current set voltage, calculated from the 8 bit set value
        """
        return self.get_value() * calibration / 255
