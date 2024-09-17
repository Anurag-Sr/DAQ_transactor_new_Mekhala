# -*- coding: utf-8 -*-

from typing import Optional, Dict
import operator as op
from functools import reduce

from swamp.gbtsca import gbtsca
from swamp.roc import roc as ROC
from swamp.SlowControl_Interface import SlowControl_Interface
from swamp.gbtsca_transport import sca_transport_tester
import swamp.gbtsca_constants as constants
import swamp.util as util

logger = util.getLogger()
util.setupLogging("DEBUG")

class Tileboard:
    def __init__(
            self,
            roc_addresses,  # [{"i2c_master": 0, "i2c_roc_address":0x28}, {"i2c_master": 1, "i2c_roc_address":0x38}]
            regmapfile: str = "swamp/regmaps/HGCROC3_sipm_I2C_params_regmap_dict.pickle",
            sca_address: int = 0x00,
            board_type: str = 'D'):
        cfg = {
            'sca_address': sca_address,
            'sc_interface': SlowControl_Interface()
        }
        logger.info('SC Interface initialized')

        transport = sca_transport_tester('sca-transport', cfg)
        transport.sendReset()
        transport.sendConnect()
        logger.debug("transport defined")

        # Initialize the GBTSCA.
        self.gbtsca = gbtsca(
            board_type=board_type,
            name='sca0',
            cfg={'address': sca_address})
        self.gbtsca.set_transport(transport)
        self.gbtsca.enableADC()
        self.gbtsca.enableDAC()
        self.gbtsca.printTemperatures()
        self.gbtsca.printVoltages()

        self.gbtsca.getDAC(0).set_voltage(1.0)
        self.gbtsca.getDAC(1).set_voltage(1.1)
        self.gbtsca.getDAC(2).set_voltage(1.2)
        self.gbtsca.getDAC(3).set_voltage(1.3)
        self.gbtsca.printDACs()

        # Enable GPIO pins of GBTSCA.
        self.gbtsca.enableGPIO()
        self.gbtsca.startupGPIO()
        self.gbtsca.printGPIOStatus()
        logger.info("GBTSCA initialized!")

        # Initialize the I2C transport of the GBT-SCA
        self.gbtsca.enableI2C()
        self.rocs = []
        for i in range(len(roc_addresses)):
            i2c_master = roc_addresses[i]["i2c_master"]
            i2c_roc_address = roc_addresses[i]["i2c_roc_address"]
            transport_i2c = self.gbtsca.getI2C(i2c_master)
            transport_i2c.enable()
            transport_i2c.configure({'clk_freq': 0}) # was clock_freq
            logger.info(f"I2C master {i2c_master} initialized!")
            roc = ROC(
                name=f"roc_s{i}",  # name MUST be consistent with the configuration file keys.
                cfg={
                    'address': i2c_roc_address,
                    'regmapfile': regmapfile,
                }
            )
            roc.set_transport(transport_i2c)
            self.rocs.append(roc)
            logger.info(f"ROC initialized on i2c master {i2c_master} at i2c address {i2c_roc_address}!")

        # Initialize the ROCs.
        logger.debug("len addresses: %d (%s)", len(roc_addresses), roc_addresses)
        if not len(roc_addresses) > 0:
            raise ValueError(
                f"Need to pass at least one address ({len(roc_addresses)} provided: "
                f"{roc_addresses})")
        logger.debug(f"len(rocs): {len(self.rocs)}")

        # Prepare storage for ROC config files during configure step.
        # Keys are the ROC names, values are the config dict.
        self._roc_config: Dict[str, Dict] = {}

    def configure(self, cfg: dict):
        # logger.debug("configure received config: %s", cfg)
        for roc in self.rocs:
            if not roc.name in cfg:
                raise KeyError(f"Could not find '{roc.name}' in configuration file.")
            # Extract the Slow Control part of the configuration file
            # corresponding to this ROC and use it to call roc.configure.
            roc_cfg = cfg[roc.name]['sc']
            # logger.debug("Configuring %s with\n%s", roc.name, roc_cfg)
            self._roc_config[roc.name] = roc_cfg
            roc.configure(roc_cfg)
            logger.info("ROC %s configured.", roc.name)
        logger.info("ROCs configured.")
        # logger.debug("roc configs:\n%s", self._roc_config)
        return "ROC(s) CONFIGURED"


    def read(self, cfg: Optional[dict] = None):
        """
        :param cfg: dict['roc_name' -> config dict]. 'sc' level should be omitted.
            For example: cfg={
                'roc_s0': {'DigitalHalf': ...},
                'roc_s1': {'DigitalHalf': ...},
            }
        """
        logger.debug("[read] received cfg:\n%s", cfg)
        # Mutable should never be passed as default arg: use None and set the default later.
        if cfg is None:
            cfg = self._roc_config
        logger.debug("[read] roc configs:\n%s", cfg)
        return {roc.name: roc.read(cfg[roc.name]) for roc in self.rocs}

    def reset_tdc(self):
        logger.debug("reset_tdc: roc names = %s", [roc.name for roc in self.rocs])
        self.configure({roc.name: {'sc': {"MasterTdc": {
            0: {"START_COUNTER": 0},
            1: {"START_COUNTER": 0},
            }}} for roc in self.rocs})
        self.configure({roc.name: {'sc': {"MasterTdc": {
            0: {"START_COUNTER": 1},
            1: {"START_COUNTER": 1},
            }}} for roc in self.rocs})
        return "masterTDCs reset."

    def dacWrite(self, channel: str, value: int):
        """
        :param channel: DAC channel, restricted to 'A', 'B', 'C', 'D'.
        """
        PINS = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        try:
            pin = PINS[channel.upper()]
        except KeyError:
            logger.error("DAC channel allowed: A, B, C, D")
            raise
        logger.info(f"DAC write {pin}, {value} (type {type(value)})")
        self.gbtsca.getDAC(pin).set_value(value)

    def dacRead(self, channel: str):
        """
        :param channel: DAC channel, restricted to 'A', 'B', 'C', 'D'.
        """
        PINS = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        try:
            pin = PINS[channel.upper()]
        except KeyError:
            logger.error("DAC channel allowed: A, B, C, D")
            raise
        return self.gbtsca.getDAC(pin).get_value()

    def adcRead(self, channel: int):
        return self.gbtsca.getADC(channel).read_value()

    def gpioGetAllPinDirection(self):
        logger.warning("'gpioGetAllPinDirection' should not be used anymore. "
                       "Use gbtsca.getGPIO(i).get_dir() instead.")
        return reduce(op.or_, [self.gbtsca.getGPIO(pin).get_dir() << pin for pin in range(0, 32)])

    def gpioSetAllPinDirection(self, direction: int):
        logger.warning("'gpioSetAllPinDirection' should not be used anymore. "
                       "The GPIO are now set during chip initialisation.")
        for pin in range(0, 32):
            self.gbtsca.getGPIO(pin).set_dir(direction & (1 << pin))

    def gpioReadAll(self):
        logger.warning("'gpioReadAll' should not be used anymore. "
                       "Use gbtsca.getGPIO(i).get_status() instead.")
        return reduce(op.or_, [self.gbtsca.getGPIO(pin).status() << pin for pin in range(0, 32)])

    def gpioWriteAll(self, vals, mask):
        logger.warning("'gpioWriteAll' should not be used anymore. "
                       "Use gbtsca.getGPIO(i).up/down() instead.")
        for pin in range(0, 31):
            if (mask >> pin) % 2 == 0:  # Select the last bit after shifting.
                # If we don't want to modify this pin, go to the next one.
                continue
            # At this point, the mask for this pin is 1, so we want to modify it.
            if (vals >> pin) % 2 == 1:
                self.gbtsca.getGPIO(pin).up()
            else:
                self.gbtsca.getGPIO(pin).down()

