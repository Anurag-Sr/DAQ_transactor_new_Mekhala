import swamp
from swamp.gbtsca import *
from swamp.gbtsca_transport import sca_transport_tester
from swamp.SlowControl_Interface import SlowControl_Interface
import swamp.roc
import yaml

# Instantiate the Interface that connects to the hardware.
sc_interface = SlowControl_Interface()

cfg = {
    'sca_address': 0x00,
    'sc_interface': sc_interface
}
print('SC Interface initialized')

transport = sca_transport_tester('sca-transport', cfg)
transport.setLoggingLevel("INFO")

sca = gbtsca('sca0', {'address': 0x00})
sca.set_transport(transport)

sca.enableADC()
adc_pin = sca.getADC(31)
print("Internal temperature reference: {:.1f}°C".format(adc_pin.read_temperature()))

sca.enableGPIO()

ldo_enable = sca.getGPIO(22)
ldo_enable.set_dir(1)
ldo_softst = sca.getGPIO(23)
ldo_softst.set_dir(1)

soft_reset_pin = sca.getGPIO(2)
soft_reset_pin.set_dir(1)
I2C_reset_pin = sca.getGPIO(3)
I2C_reset_pin.set_dir(1)

#hard_reset_pin = sca.getGPIO(4)
#hard_reset_pin.set_dir(1)


ldo_enable.up()
ldo_softst.up()
soft_reset_pin.up()
I2C_reset_pin.up()
#hard_reset_pin.up()

roc_pll_lock = sca.getGPIO(0)
roc_error = sca.getGPIO(1)

# Initialize the I2C transport of the GBT-SCA
sca.enableI2C()
transport_i2c0 = sca.getI2C(0)
transport_i2c0.enable()
transport_i2c0.configure({'clock_freq': 1})
transport_i2c1 = sca.getI2C(1)
transport_i2c1.enable()
transport_i2c1.configure({'clock_freq': 1})



print("Initialize the ROC object")
# Initialize the ROC object
roc0 = swamp.roc.roc('roc_0', {
    'address': 0x28,
    'regmapfile': 'swamp/regmaps/HGCROC3_sipm_I2C_params_regmap_dict.pickle'
})
roc0.setLoggingLevel('INFO')
roc0.set_transport(transport_i2c0)
roc0.pll_lock()

# Initialize the ROC object
roc1 = swamp.roc.roc('roc_1', {
    'address': 0x38,
    'regmapfile': 'swamp/regmaps/HGCROC3_sipm_I2C_params_regmap_dict.pickle'
})
roc1.setLoggingLevel('INFO')
roc1.set_transport(transport_i2c1)
roc1.pll_lock()


# Load a configuration on the ROC
print("Load the configuration yaml to the ROC0")
input('press enter')
with open('../swamp_test/roc_test_config0_test.yml') as file0:
    config0 = yaml.safe_load(file0)
roc0.configure(config0)

print("Load the configuration yaml to the ROC1")
input('press enter')
with open('../swamp_test/roc_test_config1_test.yml') as file1:
    config1 = yaml.safe_load(file1)
roc1.configure(config1)

# Read out the ROC status via the SCA GPIO pins
print("ROC Status: \n  - PLL locked: {} \n  - Error: {}".format(
    roc_pll_lock.status(), roc_error.status()
))

input('press enter')
print('Read-back of a register on ROC0:')
read_val0 =  roc0.read_reg(47, 11)

input('press enter')
print('Read-back of a register on ROC1:')
read_val1 =  roc1.read_reg(47, 11)


print("Status: 0x{:02X}, Reply: 0x{:02X}".format(
    (read_val0 & 0xff000000) >> 24,
    (read_val0 & 0x00ff0000) >> 16
))
print("Status: 0x{:02X}, Reply: 0x{:02X}".format(
    (read_val1 & 0xff000000) >> 24,
    (read_val1 & 0x00ff0000) >> 16
))

