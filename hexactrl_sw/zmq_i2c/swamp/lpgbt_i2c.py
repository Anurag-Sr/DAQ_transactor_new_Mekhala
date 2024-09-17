from swamp.core import Transport
import swamp.sc_lpgbt as sc_lpgbt

class lpgbt_i2c(Transport):
        
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name=name, cfg=cfg)
        self.lpgbt=None

        if 'max_packet_size' in cfg:
            self.max_packet_size = cfg['max_packet_size']
        else:
            self.max_packet_size = 256
            self.logger.info('No parameter `max_packet_size` specified. Using default value of 16.')

        try:
            self.bus = self.cfg['bus']
        except:
            self.logger.critical(f'Wrong configuration format when creating {self.logger.name} transport')
            self.logger.critical(f'Configuration used : {cfg}')
            self.logger.critical(f'Proper configuration should be a dict with "bus"')
            self.logger.critical(f'exit')
            exit(1)
        assert self.bus in range(3)
        self.setLoggingLevel('debug')

    def set_carrier(self,carrier):
        if not isinstance(carrier, sc_lpgbt.sc_lpgbt):
            self.logger.critical(f'Carrier of lpgbt_i2c object should be of type : sc_lpgbt (or of child class) instead of {type(carrier)}')
            self.logger.critical(f'exit')
            exit(1)            
        self.lpgbt=carrier

    def reset(self):
        self.logger.debug(f'Bus {self.bus} will reset')
        self.lpgbt.lpgbt.i2c_master_reset(self.bus)
        self.logger.debug(f'Bus {self.bus} reset done')

    def configure(self,cfg : dict):
        self.logger.debug(f'Lpgbt I2C master {self.bus} will configure')
        clk_freq = cfg['clk_freq'] if 'clk_freq' in cfg.keys() else 0
        scl_drive = cfg['scl_drive'] if 'scl_drive' in cfg.keys() else False
        scl_pullup = cfg['scl_pullup'] if 'scl_pullup' in cfg.keys() else False
        scl_drive_strength = cfg['scl_drive_strength'] if  'scl_drive_strength' in cfg.keys() else 0
        sda_pullup = cfg['sda_pullup'] if 'sda_pullup' in cfg.keys() else False
        sda_drive_strength = cfg['sda_drive_strength'] if  'sda_drive_strength' in cfg.keys() else 0
        self.lpgbt.lpgbt.i2c_master_config(self.bus,
                                           clk_freq,
                                           scl_drive,
                                           scl_pullup,
                                           scl_drive_strength,
                                           sda_pullup,
                                           sda_drive_strength )
        self.logger.debug(f'Lpgbt I2C master {self.bus} configuration done')

    def write_regs(self, address:int, reg_address_width:int, reg_address:int, reg_vals:list):
        self.logger.debug("in lpgbt_i2c.write_regs")

        index_max = len(reg_vals)

        for offset in range(((index_max - 1) // self.max_packet_size) + 1):
            i_addr = reg_address + offset * self.max_packet_size
            i_vals = reg_vals[offset * self.max_packet_size: min((offset + 1) * self.max_packet_size, index_max)]
            self.logger.debug(f'call i2c master write_regs with args : ({self.bus}, {address}, {reg_address_width}, {i_addr}, {i_vals})')
            self.lpgbt.lpgbt.i2c_master_write(master_id=self.bus, slave_address=address, reg_address_width=reg_address_width, reg_address=i_addr, data=i_vals )
        
        self.logger.debug("lpgbt_i2c.write_regs done")

    def read_regs(self, address:int, reg_address_width:int, reg_address:int, read_len:int):
        self.logger.debug("in lpgbt_i2c.read_regs")
        
        response = []

        for offset in range(((read_len - 1) // self.max_packet_size) + 1):
            i_addr = reg_address + offset * self.max_packet_size
            packet_size = min(self.max_packet_size, read_len - self.max_packet_size * offset)
            self.logger.debug(f'call i2c master read_regs with args : ({self.bus}, {address}, {reg_address_width}, {i_addr}, {packet_size})')
            response += self.lpgbt.lpgbt.i2c_master_read(master_id=self.bus, slave_address=address, reg_address_width=reg_address_width, reg_address=i_addr, read_len=packet_size )

        self.logger.debug(f"lpgbt_i2c.read_regs done, response = {response}")
        return response

    def write(self, address:int, val:int):
        self.logger.debug("in lpgbt_i2c.write")
        self.logger.debug(f'call i2c master single write with args : ({self.bus}, {address}, {val})')
        self.lpgbt.lpgbt.i2c_master_single_write(master_id=self.bus, slave_address=address, data=val )
        self.logger.debug("lpgbt_i2c.write done")

    def read(self, address:int):
        self.logger.debug("in lpgbt_i2c.read")
        self.logger.debug(f'call i2c master single read with args : ({self.bus}, {address})')
        response = self.lpgbt.lpgbt.i2c_master_single_read(master_id=self.bus, slave_address=address)
        self.logger.debug("lpgbt_i2c.read done")
        return response
