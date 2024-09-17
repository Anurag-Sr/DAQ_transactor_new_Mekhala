# -*- coding: utf-8 -*-

import sys
import logging
from typing import Optional, List, Dict
from threading import Thread

from swamp.gbtsca import gbtsca
from swamp.roc import roc as ROC
from swamp.SlowControl_Interface import SlowControl_Interface
from swamp.gbtsca_transport import sca_transport_tester
import swamp.gbtsca_constants as constants

logger = logging.getLogger(__name__)
FORMATTER = logging.Formatter(fmt="%(asctime)s %(levelname)-8s %(message)s")
CONSOLE_HANDLER = logging.StreamHandler(sys.stdout)
CONSOLE_HANDLER.setFormatter(FORMATTER)
logger.addHandler(CONSOLE_HANDLER)
logger.setLevel(logging.DEBUG)

class Tileboard:
    def __init__(
            self,
            roc_addresses: List[int],  # [0x28, 0x38]
            regmapfile: str = "swamp/regmaps/HGCROC3_sipm_I2C_params_regmap_dict.pickle",
            sca_address: int = 0x00):
        cfg = {
            'sca_address': sca_address,
            'sc_interface': SlowControl_Interface()
        }
        logger.info('SC Interface initialized')

        transport = sca_transport_tester('sca-transport', cfg)
        logger.debug("transport defined")

        transport.setLoggingLevel("INFO")

        # Initialize the GBTSCA.
        self.gbtsca = gbtsca('sca0', {'address': sca_address})
        self.gbtsca.set_transport(transport)
        self.gbtsca.enableADC()
        self.gbtsca.enableDAC()

        logger.info(f"==============ADC status - temperature===================")

        adc_pin = self.gbtsca.getADC(31)
        logger.info(f"GBT-SCA Temperature:: {adc_pin.read_temperature():.1f}°C")
        
        adc_pin = self.gbtsca.getADC(2)
        logger.info(f"Temperature T1:: {adc_pin.read_temperature(method='PT1000'):.1f}°C")
        
        adc_pin = self.gbtsca.getADC(0)
        logger.info(f"Temperature T2: {adc_pin.read_temperature(method='PT1000'):.1f}°C")
        
        adc_pin = self.gbtsca.getADC(4)
        logger.info(f"Temperature T3: {adc_pin.read_temperature(method='PT1000'):.1f}°C")
        
        adc_pin = self.gbtsca.getADC(1)
        logger.info(f"Temperature T4: {adc_pin.read_temperature(method='PT1000'):.1f}°C")

        adc_pin = self.gbtsca.getADC(7)
        logger.info(f"Temperature T5: {adc_pin.read_temperature(method='PT1000'):.1f}°C")

        adc_pin = self.gbtsca.getADC(3)
        logger.info(f"Temperature T6: {adc_pin.read_temperature(method='PT1000'):.1f}°C")

        adc_pin = self.gbtsca.getADC(5)
        logger.info(f"Temperature T7: {adc_pin.read_temperature(method='PT1000'):.1f}°C")

        logger.info(f"==============ADC status - voltage===================")
        
        adc_pin = self.gbtsca.getADC(8)
        logger.info(f"VCC GBT-SCA: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(18)
        logger.info(f"MPPC Bias Supply: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(9)
        logger.info(f"MPPC Bias 1: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(10)
        logger.info(f"MPPC Bias 2: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(11)
        logger.info(f"VCC Supply (10V): {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(12)
        logger.info(f"LED Bias: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(13)
        logger.info(f"VPA (2.5V HGCROC): {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(14)
        logger.info(f"PRE-VPA (3.5V): {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(15)
        logger.info(f"VDDA (1.2V HGCROC): {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(16)
        logger.info(f"VDDD (1.2V HGCROC): {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(17)
        logger.info(f"PRE-VDDA (1.5V): {adc_pin.read_voltage():.3f} V")

        logger.info(f"==============ADC status - Board ID===================")
        adc_pin = self.gbtsca.getADC(22)
        logger.info(f"PROBE_DC_L1: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(23)
        logger.info(f"PROBE_PA_L: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(24)
        logger.info(f"PROBE_DC_R1: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(25)
        logger.info(f"PROBE_PA_R: {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(26)
        logger.info(f"Board ID (LSB): {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(27)
        logger.info(f"Board ID (MSB): {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(29)
        logger.info(f"CURHV0 (ALDO): {adc_pin.read_voltage():.3f} V")

        adc_pin = self.gbtsca.getADC(30)
        logger.info(f"CURHV1 (ALDO): {adc_pin.read_voltage():.3f} V")

        logger.info(f"==============DAC status===================")
        
        dac_pin = self.gbtsca.getDAC(0)
        dac_pin.set_voltage(1.0)
        logger.info(f"REF_HV0 (21k): {dac_pin.get_voltage():.3f}V")

        
        dac_pin = self.gbtsca.getDAC(1)
        dac_pin.set_voltage(1.1)
        logger.info(f"REF_HV0 (100k): {dac_pin.get_voltage():.3f}V")

        
        dac_pin = self.gbtsca.getDAC(2)
        dac_pin.set_voltage(1.2)
        logger.info(f"REF_HV1 (21k): {dac_pin.get_voltage():.3f}V")

        
        dac_pin = self.gbtsca.getDAC(3)
        dac_pin.set_voltage(1.3)
        logger.info(f"REF_HV1 (100k): {dac_pin.get_voltage():.3f}V")

        
        # Enable GPIO pins of GBTSCA.
        self.gbtsca.enableGPIO()
        ldo_enable = self.gbtsca.getGPIO(22)
        ldo_enable.set_dir(1)
        
        ldo_softst = self.gbtsca.getGPIO(23)
        ldo_softst.set_dir(1)
        
        soft_reset_pin = self.gbtsca.getGPIO(2)
        soft_reset_pin.set_dir(1)

        hard_reset_pin = self.gbtsca.getGPIO(4)
        hard_reset_pin.set_dir(1)

        PLL_LCK_pin = self.gbtsca.getGPIO(0)
        PLL_LCK_pin.set_dir(0)

        ERROR_pin = self.gbtsca.getGPIO(1)
        ERROR_pin.set_dir(0)
        
        I2C_RSTB_pin = self.gbtsca.getGPIO(3)
        I2C_RSTB_pin.set_dir(1)
        
        PLL_LCK_2nd_ROC_pin = self.gbtsca.getGPIO(5)
        PLL_LCK_2nd_ROC_pin.set_dir(0)
        
        ERROR_2nd_ROC_pin = self.gbtsca.getGPIO(6)
        ERROR_2nd_ROC_pin.set_dir(0)
        
        LED_ON_OFF_pin = self.gbtsca.getGPIO(7)
        LED_ON_OFF_pin.set_dir(1)
        
        LED_DISABLE1_pin = self.gbtsca.getGPIO(8)
        LED_DISABLE1_pin.set_dir(1)

        LED_DISABLE2_pin = self.gbtsca.getGPIO(9)
        LED_DISABLE2_pin.set_dir(1)
        
        LED_DISABLE3_pin = self.gbtsca.getGPIO(10)
        LED_DISABLE3_pin.set_dir(1)

        LED_DISABLE4_pin = self.gbtsca.getGPIO(11)
        LED_DISABLE4_pin.set_dir(1)

        LED_DISABLE5_pin = self.gbtsca.getGPIO(12)
        LED_DISABLE5_pin.set_dir(1)

        LED_DISABLE6_pin = self.gbtsca.getGPIO(13)
        LED_DISABLE6_pin.set_dir(1)

        LED_DISABLE7_pin = self.gbtsca.getGPIO(14)
        LED_DISABLE7_pin.set_dir(1)

        LED_DISABLE8_pin = self.gbtsca.getGPIO(15)
        LED_DISABLE8_pin.set_dir(1)

        LED_DISABLE1_2nd_ROC_pin = self.gbtsca.getGPIO(16)
        LED_DISABLE1_2nd_ROC_pin.set_dir(1)

        LED_DISABLE2_2nd_ROC_pin = self.gbtsca.getGPIO(17)
        LED_DISABLE2_2nd_ROC_pin.set_dir(1)

        ENHV0_2nd_Aldo_pin = self.gbtsca.getGPIO(18)
        ENHV0_2nd_Aldo_pin.set_dir(1)

        ENHV1_2nd_Aldo_pin = self.gbtsca.getGPIO(19)
        ENHV1_2nd_Aldo_pin.set_dir(1)

        ENHV0_Aldo_pin = self.gbtsca.getGPIO(20)
        ENHV0_Aldo_pin.set_dir(1)

        ENHV1_Aldo_pin = self.gbtsca.getGPIO(21)
        ENHV1_Aldo_pin.set_dir(1)

        M50MV_VDDD_pin = self.gbtsca.getGPIO(24)
        M50MV_VDDD_pin.set_dir(1)

        P50MV_VDDD_pin = self.gbtsca.getGPIO(25)
        P50MV_VDDD_pin.set_dir(1)

        M50MV_VDDA_pin = self.gbtsca.getGPIO(26)
        M50MV_VDDA_pin.set_dir(1)

        P50MV_VDDA_pin = self.gbtsca.getGPIO(27)
        P50MV_VDDA_pin.set_dir(1)

        PG_LDO_pin = self.gbtsca.getGPIO(28)
        PG_LDO_pin.set_dir(0)      

        OCZ_LDO_pin = self.gbtsca.getGPIO(29)
        OCZ_LDO_pin.set_dir(0) 

        LED_DISABLE3_2nd_ROC_pin = self.gbtsca.getGPIO(30)
        LED_DISABLE3_2nd_ROC_pin.set_dir(1) 

        LED_DISABLE4_2nd_ROC_pin = self.gbtsca.getGPIO(31)
        LED_DISABLE4_2nd_ROC_pin.set_dir(1) 


        ldo_enable.up()
        ldo_softst.up()
        soft_reset_pin.up()
        hard_reset_pin.up()


        logger.info(f"==============GPIO status===================")
        gpio_pin = self.gbtsca.getGPIO(0)
        logger.info(f"ROC PLL Lock: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(1)
        logger.info(f"ROC Error: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(2)
        logger.info(f"SOFT_RSTB: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(3)
        logger.info(f"I2C_RSTB: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(4)
        logger.info(f"HARD_RSTB: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(5)
        logger.info(f"PLL_LCK 2nd ROC: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(6)
        logger.info(f"ERROR 2nd ROC: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(7)
        logger.info(f"LED_ON_OFF: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(8)
        logger.info(f"LED_DISABLE1: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(9)
        logger.info(f"LED_DISABLE2: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(10)
        logger.info(f"LED_DISABLE3: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(11)
        logger.info(f"LED_DISABLE4: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(12)
        logger.info(f"LED_DISABLE5: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(13)
        logger.info(f"LED_DISABLE6: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(14)
        logger.info(f"LED_DISABLE7: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(15)
        logger.info(f"LED_DISABLE8: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(16)
        logger.info(f"LED_DISABLE1 2nd ROC: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(17)
        logger.info(f"LED_DISABLE2 2nd ROC: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(18)
        logger.info(f"ENHV0 (2nd Aldo): {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(19)
        logger.info(f"ENHV1 (2nd Aldo): {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(20)
        logger.info(f"ENHV0 (Aldo): {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(21)
        logger.info(f"ENHV1 (Aldo): {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(22)
        logger.info(f"EN_LDO (VDDD, VDDA): {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(23)
        logger.info(f"SOFTSTART (VDDA, VDDD): {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(24)
        logger.info(f"M50MV_VDDD: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(25)
        logger.info(f"P50MV_VDDD: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(26)
        logger.info(f"M50MV_VDDA: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(27)
        logger.info(f"P50MV_VDDA: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(28)
        logger.info(f"PG_LDO: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(29)
        logger.info(f"OCZ_LDO: {gpio_pin.status():}")


        gpio_pin = self.gbtsca.getGPIO(30)
        logger.info(f"LED_DISABLE3 2nd ROC: {gpio_pin.status():}")

        gpio_pin = self.gbtsca.getGPIO(31)
        logger.info(f"LED_DISABLE4 2nd ROC: {gpio_pin.status():}")

        logger.info(f"===========================================")




        # Initialize the I2C transport of the GBT-SCA
        self.gbtsca.enableI2C()
        self._transport_i2c = []
        for i in range(len(roc_addresses)):
            transport_i2c = self.gbtsca.getI2C(i)
            transport_i2c.enable()
            transport_i2c.configure({'clock_freq': 1})
            self._transport_i2c.append(transport_i2c)
        logger.info("GBTSCA initialized!")

        # Initialize the ROCs.
        logger.debug("len addresses: %d (%s)", len(roc_addresses), roc_addresses)
        if not len(roc_addresses) > 0:
            raise ValueError(
                f"Need to pass at least one address ({len(roc_addresses)} provided: "
                f"{roc_addresses})")
        self.rocs = []
        for i, address in enumerate(roc_addresses):
            logger.debug("Starting setting up roc %d with address %d", i, address)
            roc = ROC(
                name=f"roc_s{i}",  # name MUST be consistent with the configuration file keys.
                cfg={
                    'address': address,
                    'regmapfile': regmapfile,
                }
            )
            logger.info("Set up ROC: %s", roc.name)
            self.rocs.append(roc)
        # self.rocs = [
        #     ROC(name=f"roc_s{i}",  # name MUST be consistent with the configuration file keys.
        #         cfg={
        #             'address': address,
        #             'regmapfile': regmapfile,
        #         }
        #     )
        #     for i, address in enumerate(roc_addresses)
        # ]
        logger.debug(f"len(rocs): {len(self.rocs)}")
        for i, roc in enumerate(self.rocs):
            roc.setLoggingLevel('DEBUG')
            roc.set_transport(self._transport_i2c[i])
            roc.pll_lock()

        logger.info("ROC initialized!")

        # Prepare storage for ROC config files during configure step.
        # Keys are the ROC names, values are the config dict.
        self._roc_config: Dict[str, Dict] = {}

    def configure(self, cfg: dict):
        threads = []
        for roc in self.rocs:
            if not roc.name in cfg:
                raise KeyError(f"Could not find '{roc.name}' in configuration file.")
            # Extract the Slow Control part of the configuration file
            # corresponding to this ROC and use it to call roc.configure.
            roc_cfg = cfg[roc.name]['sc']
            logger.debug("Configuring %s with\n%s", roc.name, roc_cfg)
            self._roc_config[roc.name] = roc_cfg
            thread = Thread(target=roc.configure, args=(roc_cfg,), name=roc.name)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        logger.info("ROCs configured.")
        logger.debug("roc configs:\n%s", self._roc_config)
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
        self.configure({roc.name: {'sc': {"MasterTdc": {"all": {"START_COUNTER": 0}}}}} for roc in self.rocs)
        self.configure({roc.name: {'sc': {"MasterTdc": {"all": {"START_COUNTER": 1}}}}} for roc in self.rocs)
        return "masterTDCs reset."

    def dacWrite(self, channel: str, value: int):
        """
        :param channel: DAC channel, restricted to 'A', 'B', 'C', 'D'.
        """
        try:
            pin = constants.DAC[f"W_{channel.upper()}"]
        except KeyError:
            logger.error("DAC channel allowed: A, B, C, D")
            raise
        self.gbtsca.getDAC(pin).set_value(value)

    def dacRead(self, channel: str):
        """
        :param channel: DAC channel, restricted to 'A', 'B', 'C', 'D'.
        """
        try:
            pin = constants.DAC[f"R_{channel.upper()}"]
        except KeyError:
            logger.error("DAC channel allowed: A, B, C, D")
            raise
        return self.gbtsca.getDAC(pin).get_value()

    def adcRead(self, channel: int):
        return self.gbtsca.getADC(channel).read_value()
    
    def gpioSetDirection(self, direction: int):
        self.gbtsca.getGPIO(constants.GPIO["CHANNEL"]).set_dir(direction)

    def gpioGetDirection(self):
        return self.gbtsca.getGPIO(constants.GPIO["CHANNEL"]).get_dir()
    
    def gpioRead(self):
        return self.gbtsca.getGPIO(constants.GPIO["CHANNEL"]).status()

    def gpioWrite(self, vals, mask):

        raise NotImplementedError