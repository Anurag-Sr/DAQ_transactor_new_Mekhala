from swamp.core import Transport
#from gbtsca_transport import I2CRxPayload

class gbtsca_i2c(Transport):
    """
    The class represents an I2C master of the GBT-SCA.

    Attributes:
        master (int): index of this I2C master
        channel (int): GBT-SCA channel that this master is in (see table 4.1 in
            the GBT-SCA manual).
        control_reg (int): Control register of the GBT-SCA that is used to
            enable and disable this I2C master (see tables 5.3 to 5.5 in the
            GBT-SCA manual).
        control_mask (int): Bit in the GBT-SCA control register (control_reg)
            that corresponds to this I2C master.
        carrier (SwampObject): Inherited from swamp Transport
    """

    def __init__(self, name : str="", cfg : dict={} ):
        """
        Args:
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary

        Configuration parameters:
            pin (int): The index of the I2C master that this object represents.
        """
        super().__init__(name=name, cfg=cfg)
        assert cfg["pin"] >= 0 and cfg["pin"] < 16
        self.master = cfg["pin"]
        self.channel = self.master + 0x03
        if self.master < 5: # Control register B
            self.control_reg = 0x02
            self.control_mask = 1 << (self.master + 3 + 24)
        elif self.master < 13: # Control register C
            self.control_reg = 0x04
            self.control_mask = 1 << (self.master - 5 + 24)
        else: # Control register D
            self.control_reg = 0x06
            self.control_mask = 1 << (self.master - 13 + 24)

    def enable(self):
        """
        Enable this I2C master.
        """
        self.carrier.transport.modifyControlRegister(0x00, self.control_reg, 1, self.control_mask)

    def disable(self):
        """
        Disable this I2C master.
        """
        self.carrier.transport.modifyControlRegister(0x00, self.control_reg, 1, self.control_mask, enable=False)

    def configure(self, cfg : dict):
        """
        Configure this I2C master. 

        Args:
            cfg (dict): Configuration dictionary.

        Configuration parameters:
            clk_freq (int): Select the communication speed.
                FREQ = 00 -> 100kHz
                FREQ = 01 -> 200kHz
                FREQ = 10 -> 400kHz
                FREQ = 11 -> 1MHz
        """
        if "clk_freq" in cfg:
            self.carrier.transport.modifyControlRegister(self.channel, 0x30, 1, cfg["clk_freq"] << 24)

    def write(self, address:int, val:int):
        """
        Send a write command on I2C.

        Args:
            address (int): Address to write to
            val (int): Value to write

        Returns:
            int: Respone from the I2C client.
        """
        self.carrier.transport.clearCommands()
        self.carrier.transport.addCommand(self.channel, 0x82, 4, (address << 24) + (val << 16))
        return self.carrier.transport.dispatchCommands()[0]['payload']

    def read(self, address:int):
        """
        Read the value of a register via I2C.

        Args:
            address (int): Address to read from

        Returns:
            int: Response from the I2C client.
        """
        self.carrier.transport.clearCommands()
        self.carrier.transport.addCommand(self.channel, 0x86, 4, address << 24)
        contents=self.carrier.transport.dispatchCommands()[0]['payload']
        status=(contents>>24)&0xFF
        if status!=0x4:
            if status&0x08:
                raise ValueError("Error: i2c_read failure due to SDA low at start of transaction")
            if status&0x40:
                raise ValueError("Error: i2c_read failure due to NOACK")
            raise ValueError("Error: i2c_read failure 0x%02x"%status)
        return (contents>>16)&0xFF

    def write_regs(self, address:int, reg_address_width:int, reg_address:int, reg_vals:list):
        """
        Write multiple addresses via I2C.

        TODO: Not implemented
        """
        raise NotImplementedError("Error: write_regs not implemented")

    def read_regs(self, address:int, reg_address_width:int, reg_address:int, read_len:int):
        """
        Read multiple addresses via I2C.

        TODO: Not implemented
        """
        raise NotImplementedError("Error: read_regs not implemented")
