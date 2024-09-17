import swamp.util as util

class SwampObject:
    def __init__(self, name : str="", cfg : dict={} ):
        self.name=name
        self.cfg=cfg
        self.logger = util.getLogger(self.name)

    def __str__(self):
        pass

    def __eq__(self,other):
        return other is not None and self.name==other.name

    def setLoggingLevel(self,level):
        util.setLoggingLevel(level,self.logger)

class Transport(SwampObject):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        self.carrier=None

    def set_carrier(self,carrier):
        self.carrier=carrier

    def __str__(self):
        return f'Transport Name : {self.name}, Config: {self.cfg}, Carrier : {self.carrier.name}' if self.carrier is not None \
            else f'Transport Name : {self.name}, Config: {self.cfg}, Carrier : {self.carrier}'

    def write_regs(self, address:int, reg_address_width:int, reg_addr:int, reg_vals:list):
        self.logger.critical(f'write_regs function of {self.name} is not implemented')
    
    def read_regs(self, address:int, reg_address_width:int, reg_addr:int, read_len:int):
        self.logger.critical(f'read_regs function of {self.name} is not implemented')
    
    def write(self, addr:int, reg_val:int):
        self.logger.critical(f'write function of {self.name} is not implemented')
    
    def read(self, addr:int):
        self.logger.critical(f'read function of {self.name} is not implemented')
    
class Chip(SwampObject):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)

        try:
            self.address=cfg['address']
        except Exception as e:
            self.logger.critical(f'Error when initialize {self.name}, "address" should be given in config : {cfg}')
            self.logger.critical(f'Exception : {str(e)}')
            self.logger.critical(f'The process will exit')
            exit(1)

        self.electronic_id = -1
        if 'electronic_id' in cfg.keys():
            self.electronic_id = cfg['electronic_id']
        
        self.transport=None
        self.reset_pin=None
        self.is_sc_power_on_value=False
        self.cache={}
        
    def set_transport(self,transport):
        if not isinstance(transport, Transport):
            self.logger.critical(f'Transport of {self.name} object should be of type : transport (or of child class) instead of {type(transport)}')
            self.logger.critical(f'exit')
            exit(1)            
        self.transport=transport

    def set_reset_pin(self,reset_pin):
        if not isinstance(reset_pin, GPIO):
            self.logger.critical(f'Reset pin of roc object should be of type : lpgbt_gpio (or of child class) instead of {type(reset_pin)}')
            self.logger.critical(f'exit')
            exit(1)            
        self.reset_pin=reset_pin

    def __str__(self):
        if self.reset_pin is not None and self.transport is not None:
            return f'Chip Name : {self.name}, Config: {self.cfg}, Transport : {self.transport.name}, Reset : {self.reset_pin.name}'
        elif self.transport is not None:
            return f'Chip Name : {self.name}, Config: {self.cfg}, Transport : {self.transport.name}, Reset : {self.reset_pin}'
        else:
            return f'Chip Name : {self.name}, Config: {self.cfg}, Transport : {self.transport}'

    def reset(self):
        #self.reset_pin.down()
        #need to sleep?
        self.cache = {}
        self.is_sc_power_on_value=True
        #self.reset_pin.up()

    def configure(self, cfg: dict, read_back: bool=False):
        self.logger.info(f'configure with config = {cfg}')

    def read(self, cfg: dict={}, from_cache: bool=False):
        self.logger.info(f'read with config = {cfg}')
    # def reset(self):
    #     self.logger.debug(f'in {self.name}.reset()')
    #     self.logger.debug(f'reset pin = {self.reset_pin}')

    #     if self.reset_pin is None:
    #         self.logger.critical(f'{self.name} does not have a defined reset pin')
    #         self.logger.critical(f'{self.name}.reset will be skipped')
    #         return

    #     self.logger.debug(f'setting down {self.name} reset pi')
    #     self.reset_pin.down()
    #     while not self.reset_pin.is_down():
    #         self.reset_pin.down()

    #     self.logger.debug(f'setting up {self.name} reset pin')
    #     while not self.reset_pin.is_up():
    #         self.reset_pin.up()
    #     self.logger.debug(f'{self.name}.reset done')

    def reset_cache(self):
        self.cache={}
    
class GPIO(SwampObject):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        self.carrier=None

    def __eq__(self,other):
        return other is not None and self.name==other.name and self.pin==other.pin

    def set_carrier(self,carrier):
        self.carrier=carrier

    def __str__(self):
        return f'GPIO line : {self.name}, Config: {self.cfg}, Carrier : {self.carrier.name}' if self.carrier is not None \
            else f'GPIO line : {self.name}, Config: {self.cfg}, Carrier : {self.carrier}'

class ADC(SwampObject):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        self.carrier=None

    def __eq__(self,other):
        return self.name==other.name and self.channel==other.channel

    def set_carrier(self,carrier):
        self.carrier=carrier

    def __str__(self):
        return f'ADC channel : {self.name}, Config: {self.cfg}, Carrier : {self.carrier.name}' if self.carrier is not None \
            else f'ADC channel : {self.name}, Config: {self.cfg}, Carrier : {self.carrier}'
    
class lpgbt_ic(Transport):
    pass
class lpgbt_ec(Transport):
    pass

class lpgbt_ic_emp(Transport):
    pass
class lpgbt_ec_emp(Transport):
    pass

class lpgbt_i2c(Transport):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        self.nwrite=0
        self.nread=0
        self.fout = open('output.txt','w')
        pass
    
    def write(self,address,val):
        self.nwrite+=1
        self.fout.write(f'writing addr,val : {address},{val}\n') 

    def read(self,address):
        self.nread+=1
        self.fout.write(f'reading addr : {address}\n') 
        return 0xca

class sc_lpgbt(Chip):
    def minimal_initialization(self):
        if 'daq' in self.name:
            self.logger.info('setup_core_d')
            self.logger.info('setup_clock')
            self.logger.info('init_gpio')
            self.logger.info('init_inputs_d')
            self.logger.info('init_outputs')
            self.logger.info('powerup2')
        if 'trg_w' in self.name:
            self.logger.info('setup_core_w')
            self.logger.info('init_gpio')
            self.logger.info('init_inputs_w')
            self.logger.info('powerup2')
        if 'trg_e' in self.name:
            self.logger.info('setup_core_e')
            self.logger.info('init_gpio')
            self.logger.info('init_inputs_e')
            self.logger.info('powerup2')
        
class vtrx(Chip):
    pass

class roc(Chip):
    pass

class econ(Chip):
    pass

class lpgbt_gpio_pin(GPIO):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        self.chips = []
        
    def __str__(self):
        return f'GPIO line : {self.name}, Config: {self.cfg}, Carrier : {self.carrier.name}' if self.carrier is not None \
            else f'GPIO line : {self.name}, Config: {self.cfg}, Carrier : {self.carrier}'

    def up(self):
        self.logger.info(f'GPIO line : {self.name} going up')

    def down(self):
        self.logger.info(f'GPIO line : {self.name} going down')
        
class lpgbt_gpio_reset_pin(lpgbt_gpio_pin):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name,cfg)
        self.chips = []
        
    def register_chip(self,chip : Chip):
        self.chips.append(chip)
        chip.set_reset_pin(self)

    def __str__(self):
        return f'GPIO line : {self.name}, Config: {self.cfg}, Carrier : {self.carrier.name}, Chips = {[chip.name for chip in self.chips]}' if self.carrier is not None \
            else f'GPIO line : {self.name}, Config: {self.cfg}, Carrier : {self.carrier}'
