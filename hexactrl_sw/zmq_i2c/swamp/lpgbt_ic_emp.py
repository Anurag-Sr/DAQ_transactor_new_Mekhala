import swamp.util as util
from swamp.core import Transport
from math import ceil
from swamp.emp_interface import emp_interface, emp_transport


class lpgbt_ic_emp(emp_transport):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name=name, cfg=cfg)
        self.transactor.set_IC()

    def write_regs(self, address:int, reg_address_width:int, reg_address:int, reg_vals:list, protocol="IC"):
        if protocol== "IC":
            self.transactor.set_IC()
        else:
            self.transactor.set_EC()

        ## reg_address_width is not used as the transactor reserves 16 bits for the reg_address
        ## we need to keep it to use same interface as lpgbt_i2c.write_regs function (which might be used to configure lpgbts)
        self.logger.debug("in lpgbt_ic_emp.write_regs")
        n_regs = len(reg_vals)

        # split registers in transactions
        n_transactions = ceil(n_regs/16) # up to 16 registers per transaction
        
        for i in range(n_transactions):
            status = self.transactor.write_IC(reg_address + i*16, reg_vals[i*16 : (i+1)*16], address)  
        self.logger.debug("lpgbt_ic_emp.write_regs done")
        
    def read_regs(self, address:int, reg_address_width:int, reg_address:int, read_len:int, protocol="IC"):
        if protocol== "IC":
            self.transactor.set_IC()
        else:
            self.transactor.set_EC()
        ## reg_address_width is not used as the transactor reserves 16 bits for the reg_address
        ## we need to keep it to use same interface as lpgbt_i2c.read_regs function (which might me used to read from lpgbts)
        self.logger.debug("in lpgbt_ic.read_regs")

        # split registers in transactions
        n_transactions = ceil(read_len/16) # up to 16 registers per transaction
        response = []
        for i in range(n_transactions):
            res_temp = []
            if i != n_transactions -1:
                res_temp = self.transactor.read_IC(reg_address + (i*16), 16, address)
                self.logger.debug(f'n_transaction = {i}, response = {res_temp}')
            else:
                res_temp = self.transactor.read_IC(reg_address + (i*16), (read_len % 16), address)
                self.logger.debug(f'n_transaction = {i}, response = {res_temp}')
            response.extend(res_temp)
        
        self.logger.debug("lpgbt_ic.read_regs done")
        return response

class lpgbt_ec_emp(lpgbt_ic_emp):   
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name=name, cfg=cfg)
        self.transactor.set_EC()

    def write_regs(self, address:int, reg_address_width:int, reg_address:int, reg_vals:list):
        self.logger.debug("in lpgbt_ec.write_regs")
        super().write_regs(address, reg_address_width, reg_address, reg_vals, "EC")
        self.logger.debug("lpgbt_ec.write_regs done")
        
    def read_regs(self, address:int, reg_address_width:int, reg_address:int, read_len:int):
        self.logger.debug("in lpgbt_ec.read_regs")
        resp = super().read_regs(address, reg_address_width, reg_address, read_len, "EC")
        self.logger.debug("lpgbt_ec.read_regs done")
        return resp