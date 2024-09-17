import swamp.util as util
from swamp.core import Transport
from swamp.transactorEncoding import encoder
from swamp.transactorDecoding import decoder
from math import ceil
from swamp.sc_transactor_interface import sc_transactor_interface

class lpgbt_ic(Transport):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name=name, cfg=cfg)
        try:
            self.broadcast_address = self.cfg['broadcast_address']
        except:
            self.logger.critical(f'Wrong configuration format when creating {self.name} transport')
            self.logger.critical(f'Configuration used : {cfg}')
            self.logger.critical(f'Proper configuration should be a dict with broadcast_address ')
            self.logger.critical(f'exit')
            exit(1)

        self.encoder = encoder()
        self.decoder = decoder()
        self.transactor = sc_transactor_interface()
        self.reply_address = util.get_lsb_id(self.broadcast_address)
        
    def setLoggingLevel(self,level):
        super().setLoggingLevel(level)
        self.encoder.setLoggingLevel(level)
        self.decoder.setLoggingLevel(level)

    def execute_transactions(self):
        self.transactor.execute_transactions()

    def write_regs(self, address:int, reg_address_width:int, reg_address:int, reg_vals:list):
        ## reg_address_width is not used as the transactor reserves 16 bits for the reg_address
        ## we need to keep it to use same interface as lpgbt_i2c.write_regs function (which might me used to configure lpgbts)
        self.logger.debug("in lpgbt_ic.write_regs")
        encodedData = []
        n_regs = len(reg_vals)
        n_transactions = ceil(n_regs/8) # up to 8 registers per transaction
        ## should check n_transactions is less than 1024 -> otherwise need to split; don't see a case for this yet
        for i in range(n_transactions):
            payload = 0
            index=0
            for val in reg_vals[8*i : 8*(i+1)]:
                payload = payload | (val << 8*index)
                index = index+1
            nbytes = 8 if i+1 < n_transactions else index
            read_write = 0 # aka write
            self.logger.debug(f'broadcast address={self.broadcast_address}; reply address={self.reply_address}, chip address={address}, read write = {read_write}, register = {reg_address + 8*i}, nbytes = {nbytes}')
            encodedData += self.encoder.encode(self.broadcast_address, self.reply_address, address, read_write, reg_address + 8*i, nbytes, payload)

        ##TO REMOVE##
        #for first, second, third, fourth in zip(encodedData[::4], encodedData[1::4], encodedData[2::4], encodedData[3::4]):
        #    self.logger.debug(f'{hex(first): <15}{hex(second): <15}{hex(third): <15}{hex(fourth)}')
        #############
        
        encodedResponse = self.transactor.send(encodedData)
        #assert len(encodedResponse)==n_transactions*4
        #for i in range(n_transactions):
        #    response = self.decoder.decode( encodedResponse[4*i:4*(i+1)] )
        #    self.logger.debug(f'response = {response}')
        
        self.logger.debug("lpgbt_ic.write_regs done")
        
    def read_regs(self, address:int, reg_address_width:int, reg_address:int, read_len:int):
        ## reg_address_width is not used as the transactor reserves 16 bits for the reg_address
        ## we need to keep it to use same interface as lpgbt_i2c.read_regs function (which might me used to read from lpgbts)
        self.logger.debug("in lpgbt_ic.read_regs")
        encodedData = []
        n_transactions = ceil(read_len/8) # up to 8 registers per transaction
        ## should check n_transactions is less than 1024 -> otherwise need to split; don't see a case for this yet
        for i in range(n_transactions):
            payload = 0
            nbytes = 8 if i+1 < n_transactions else read_len%8
            read_write = 1 # aka read
            self.logger.debug(f'broadcast address={self.broadcast_address}; reply address={self.reply_address}, chip address={address}, read write = {read_write}, register = {reg_address + 8*i}, nbytes = {nbytes}')
            encodedData += self.encoder.encode(self.broadcast_address, self.reply_address, address, read_write, reg_address + 8*i, nbytes, payload)
        
        encodedResponse = self.transactor.send_recv(encodedData)
        assert len(encodedResponse)==n_transactions*4
        response = []
        for i in range(n_transactions):
            block = self.decoder.decode( encodedResponse[4*i:4*(i+1)] )
            nbytes = 8 if i+1 < n_transactions else read_len%8
            reg_vals = [ (block['payload']>>8*i)&0xFF for i in range(nbytes) ]
            response.extend(reg_vals)
        self.logger.debug(f'response = {response}')
        self.logger.debug("lpgbt_ic.read_regs done")
        return response

class lpgbt_ec(lpgbt_ic):        
    def write_regs(self, address:int, reg_address_width:int, reg_address:int, reg_vals:list):
        self.logger.debug("in lpgbt_ec.write_regs")
        super().write_regs(address, reg_address_width, reg_address, reg_vals)
        self.logger.debug("lpgbt_ec.write_regs done")
        
    def read_regs(self, address:int, reg_address_width:int, reg_address:int, read_len:int):
        self.logger.debug("in lpgbt_ec.read_regs")
        resp = super().read_regs(address, reg_address_width, reg_address, read_len)
        self.logger.debug("lpgbt_ec.read_regs done")
        return resp
