from smbus2 import SMBus
import gpiod

class LinkBuilder:
    def __init__(self):

       i2cs = {}
       gpios = {}
  
       try:
           i2cs.update(xil_i2c_discover())
           gpios.update(xil_gpio_discover())
       except (IOError):
           pass

       try:
          import gbtsca_bus
          try:
             self.sca = gbtsca_bus.GBTSCA("gbt_sca_com_0","file://${UHAL_ADDRESS_TABLE}/connection.xml", "mylittlememory")
             self.sca.reset_gbtsca() 
          except(gbtsca_bus.sca.gbtsca_exception.GBT_SCA_Exception):
             pass
          
          try:
              gpios.update(sca_gpio_discover(self.sca))
              for gpio_name, gpio in gpios.items():
                 gpio.write(1)
              i2cs.update(sca_i2c_discover(self.sca))
          except(gbtsca_bus.sca.gbtsca_exception.GBT_SCA_Exception):
              pass

       except(ImportError):
          pass

       self.links = {}
       for gpio_name, gpio in gpios.items():
           for i2c_name, i2c in i2cs.items():
               if gpio_name in i2c_name:
                   self.links[i2c_name] = Link(i2c, gpio)

class Link:
    def __init__(self, i2c, gpio):
        self.i2c = i2c
        self.gpio = gpio

class i2c():
    def __init__(self, addr, bus, sca=0):
        self._addr = addr
        self._bus = bus
        self._sca = sca

    def write(self, *args, **kwargs):
        raise NotImplementedError

    def read(self, *args, **kwargs):
        raise NotImplementedError

class sca_i2c(i2c):
    def write(self, offset, byte):
       with self._sca.scabus(self._bus) as bus:
            bus.write_byte(self._addr + offset, byte)
       return None
    
    def read(self, offset):
       with self._sca.scabus(self._bus) as bus:
            ret = bus.read_byte(self._addr + offset)
       return ret

def sca_i2c_discover(sca):
    """ Discover all ROCs on gbtsca i2c """

    rocs = []
    sca.enableI2C(0xffff)
    for bus_id in range(1):  # was 15 before, July2023, 8 i2c bus lines
        try:
            with sca.scabus(bus_id) as bus:
                addrs = []
                for addr in range(128):  # 128 addrs per bus line
                    try:
                        bus.read_byte(addr)
                        addrs.append(addr)
                    except Exception as e:
                        pass # skip non-existing addr
                print('[I2C] Found %d address(es) on bus %d' % (len(addrs),bus_id))
                if len(addrs) >= 8: 
                    rocs.append((addrs[0], bus_id))
                if len(addrs) == 16:
                    rocs.append((addrs[8], bus_id))
        except Exception as e:
            pass  # skip undefined i2c busses
    return sca_i2c_create(rocs,sca)

def sca_i2c_create(rocs,sca):
    """ Detect board type & create i2c objects """

    n = len(rocs)
    if n == 1:   
        print('[I2C] Identified Single-Chip (Char) board')
        roc_map = i2c_char_map
    elif n == 3: 
        print('[I2C] Identified LD HexaBoard')
        roc_map = i2c_ld_map
    elif n == 6: 
        print('[I2C] Identified HD HexaBoard')
        roc_map = i2c_hd_map
    return {roc_map[addr]:sca_i2c(addr,bus,sca) for (addr, bus) in rocs}

class xil_i2c(i2c):
    def write(self, offset, byte):
        with SMBus(self._bus) as bus:
            bus.write_byte(self._addr + offset, byte)
        return None

    def read(self, offset):
        with SMBus(self._bus) as bus:
            ret = bus.read_byte(self._addr + offset)
        return ret

i2c_char_map = {0x28: 'roc_s0'}
i2c_ld_map_v1 = {0x00: 'roc_s0', 0x40: 'roc_s1', 0x20: 'roc_s2'} #old LD boards for ROCv2
i2c_ld_map_v2 = {0x60: 'roc_s0', 0x40: 'roc_s1', 0x20: 'roc_s2'} #nsh boards
i2c_ld_map_v3 = {0x08: 'roc_s0', 0x18: 'roc_s1', 0x28: 'roc_s2'} #LD V3 boards

# i2c_hd_map = {0x18: 'roc_s0_0', 0x30: 'roc_s0_1', 0x08: 'roc_s1_0', 0x20: 'roc_s1_1', 0x10: 'roc_s2_0', 0x28: 'roc_s2_1'}
i2c_hd_map = {0x8: 'roc_s0_0', 0x48: 'roc_s0_1', 0x18: 'roc_s1_0', 0x58: 'roc_s1_1', 0x28: 'roc_s2_0', 0x68: 'roc_s2_1'}

def xil_i2c_discover():
    """ Discover all ROCs on i2c """

    rocs = []
    for bus_id in range(8):  # 8 i2c bus lines
        try:
            with SMBus(bus_id) as bus:
                addrs = []
                for addr in range(128):  # 128 addrs per bus line
                    try:
                        bus.read_byte(addr)
                        addrs.append(addr)
                    except IOError as e: 
                        pass # skip non-existing addr
                print('[I2C] Found %d address(es) on bus %d' % (len(addrs),bus_id))
                if len(addrs) >= 8: 
                    rocs.append((addrs[0], bus_id))
                if len(addrs) >= 16:
                    rocs.append((addrs[8], bus_id))
                if len(addrs) >= 24:
                    rocs.append((addrs[16], bus_id))
        except FileNotFoundError:
            pass  # skip undefined i2c busses
    return xil_i2c_create(rocs)

def xil_i2c_create(rocs):
    """ Detect board type & create i2c objects """

    n = len(rocs)
    print(rocs)
    if n == 1:   
        print('[I2C] Identified Single-Chip (Char) board')
        roc_map = i2c_char_map
    elif n == 3: 
        print('[I2C] Identified LD HexaBoard')
        if rocs[0][0] in i2c_ld_map_v1:
            i2c_map = i2c_ld_map_v1
        elif rocs[0][0] in i2c_ld_map_v2:
            i2c_map = i2c_ld_map_v2
        elif rocs[0][0] in i2c_ld_map_v3:
            i2c_map = i2c_ld_map_v3
        else:
            print("ERROR : fail to find correct I2C map in xil_i2c_create")
            i2c_map = {}
        roc_map = i2c_map
    elif n == 6: 
        print('[I2C] Identified HD HexaBoard')
        roc_map = i2c_hd_map
    return {roc_map[addr]:xil_i2c(addr,bus) for (addr, bus) in rocs}

class gpio():
    def __init__(self, lines):
        self._lines = lines

    def write(self, *args, **kwargs):
        raise NotImplementedError
    
    def read(self, *args, **kwargs):
        raise NotImplementedError

gpio_tbtester_map = {'roc_s0':[('hgcroc_soft_rstB',0x4), ('hgcroc_i2c_rstB',0x8), ('hgcroc_hard_rstB',0x10)]}
gpio_tbtester_noresetmap = {'roc_s0':[('EN_LDO',0x400000), ('SOFTSTART',0x800000)]}

class sca_gpio(gpio):
    def write(self, val):
       for line in self._lines:
            line.set_value(val)
  
    def read(self):
        ans = { }
        for line in self._lines:
            ans[line.name] = line.get_value()
        return ans
 
    def reset(self):
        self._lines[0].reset_rocs()

def sca_gpio_discover(sca):
    lines = []
    sca.enableGPIO(True)
    for name in gpio_tbtester_map['roc_s0']:
        lines.append(sca.gpio(name[0],name[1],False));
    for name in gpio_tbtester_noresetmap['roc_s0']:
        line = sca.gpio(name[0],name[1],False)
        line.set_value(1)
    return {'roc_s0' : sca_gpio(lines)}   

class xil_gpio(gpio):

    def write(self, val):
        for line in self._lines:
            config = gpiod.line_request()
            config.consumer = "xil_gpio_write"
            config.request_type = gpiod.line_request.DIRECTION_OUTPUT
            line.request(config)
            line.set_value(val)
            line.release()

    def read(self):
        ans = {}
        for line in self._lines:
            config = gpiod.line_request()
            config.consumer = "xil_gpio_read"
            config.request_type = gpiod.line_request.DIRECTION_INPUT
            line.request(config)
            ans[line.name] = line.get_value()
        return ans

gpio_char_map = {'roc_s0': ['hgcroc_rstB', 'resyncload', 'hgcroc_i2c_rstB']}

## for trophy v1 and v2
gpio_hexa_map_v1 = {'roc_s0': ['s0_resetn', 's0_i2c_rstn'], 
                    'roc_s1': ['s1_resetn', 's1_i2c_rstn'], 
                    'roc_s2': ['s2_resetn', 's2_i2c_rstn']}

## for trophy v3
gpio_hexa_map_v3 = {'roc_s0': ['s1_resetn', 'hard_resetn'], 
                    'roc_s1': ['s2_resetn', 'hard_resetn'], 
                    'roc_s2': ['s3_resetn', 'hard_resetn']}

def xil_gpio_discover():
    # get all lines on all connected gpio chips
    lines = []
    for chip in gpiod.chip_iter():
        for line in gpiod.line_iter(chip):
            lines.append(line)
    print([l.name for l in lines],'hgcroc_rstB' in [l.name for l in lines])        
    if 'hgcroc_rstB' in [l.name for l in lines]:
        gpio_map = gpio_char_map
    elif 's0_i2c_rstn' in [l.name for l in lines]:
        gpio_map = gpio_hexa_map_v1
    elif 'hard_resetn' in [l.name for l in lines]:
        gpio_map = gpio_hexa_map_v3
    else:
        print("ERROR : fail to find correct GPIO map in xil_gpio_discover")
        gpio_map = {}

    print("[GPIO] Identified gpio map : ",gpio_map)
    ret = {}
    print(gpio_map)
    for roc, line_names in gpio_map.items():
        sel_names = set(line_names).intersection([l.name for l in lines])
        if sel_names:
            ret[roc] = xil_gpio([l for l in lines if l.name in sel_names])
    if ret: return ret
    else: raise('Missing HexaBoard GPIO lines.')
