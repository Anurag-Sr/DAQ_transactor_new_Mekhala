from swamp.core import Transport
from swamp import gbtsca_tx, gbtsca_rx

class sca_transport(Transport):
    """
    Abstract transport class for communication with the GBT-SCA. Defines 
    all methods that are needed for the communication.

    Implementations of this class can be for any firmware transactor (e.g.
    EMP or on a Tileboard Tester). 

    The general idea is that you add commands to a list and dispatch them
    all at once. This works better with the GBT-SCA protocol than read/write
    methods.

    Additionally, there is a method to read-modify-write a register.

    Attributes:
        sca_address (int): Address of the GBT-SCA
    """

    def __init__(self, name : str="", cfg : dict={}):
        """
        Args:
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary

        Configuration parameters:
            sca_address (int): Address of the GBT-SCA. Defaults to 0.
        """
        super().__init__(name, cfg)
        self.sca_address = cfg.get("sca_address", 0)

    def sendReset(self):
        pass

    def sendConnect(self):
        pass

    def addCommand(self, channel, command, length=1, data=0):
        """
        Add a command to the list of commands. This method should not *send*,
        that should happen with dispatchCommands.

        Args:
            channel (int): channel of the GBT-SCA (see table 4.1 in the GBT-SCA
                manual)
            command (int): command code for this channel (typically described
                in the last table of each chapter in the GBT-SCA manual)
            length (int): Length of the payload data in bytes. Default is 1.
            data (int): payload data. Default is 0.
        """
        pass

    def clearCommands(self):
        """
        Clear the list of commands without sending them to the GBT-SCA.
        """
        pass

    def dispatchCommands(self):
        """
        Send the commands in the queue and clear the command list.

        Returns:
            A list of the replies for all commands.
        """
        pass

    def modifyControlRegister(self, sca_ch, reg_addr, length, mask, enable=True):
        """
        Convenience method to read-modify-write a control register. 

        Args:
            sca_ch (int): channel of the GBT-SCA (see table 4.1 in the GBT-SCA
                manual)
            reg_addr (int): Register in this channel to modify.
            length (int): Length in bytes of the register to modify.
            mask (int): bit mask of which bits to modify
            enable (bool): if set to true, the masked bits will be set to 1.
                If false, the masked bits will be set to 0. Default is true.
        """

        # Clear the command list to avoid unexpected commands
        self.clearCommands()

        # Read the current value of the register
        self.addCommand(sca_ch, reg_addr+1)
        reply = self.dispatchCommands()

        # Check if operation was successful
        if reply is None:
            raise Exception("Reading of register 0x{:02x}:0x{:02x} failed!".format(sca_ch, reg_addr+1))

        # Set the new value
        current_register = reply[0]['payload']
        if enable:
            new_register = current_register | mask
        else:
            new_register = current_register & (mask ^ 0xffffffff)

        self.logger.debug("modifyControlRegister: 0x{:032b} -> 0b{:032b}".format(
            current_register, new_register
        ))

        # Update the register value if necessary
        if new_register != current_register:
            self.addCommand(sca_ch, reg_addr, length, new_register)
            self.dispatchCommands()



class sca_transport_tester(sca_transport):
    """
    Implementation of the GBT-SCA transport class for the firmware transactor
    that is used in the tileboard tester.

    Attributes:
        sca_address (int): Address of the GBT-SCA, inherited from sca_transport
        broadcast_address (int)
        reply_address (int)
        free_transaction_ids (list): List of free transaction IDs. Don't modify
    """
    def __init__(self, name : str="", cfg : dict={}):
        """
        Args:
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary

        Configuration parameters:
            sca_address (int): Address of the GBT-SCA. Defaults to 0.
            sc_interface: Instance of the slow control interface for the
                firmware transactor.
        """
        super().__init__(name=name, cfg=cfg)
        self.sc_interface = cfg['sc_interface']
        if 'repl_address' in cfg:
            self.reply_address=cfg['repl_address']
        else:
            self.reply_address=0
        self.logger.info("Using reply address: %s", self.reply_address)
        if 'bst_address' in cfg:
            self.broadcast_address=cfg['bst_address']
        else:
            self.broadcast_address=1<<(self.reply_address)
        self.logger.info("Using broadcast address: %s", self.broadcast_address)
        self.sca_address = cfg['sca_address']
        self.logger.info("Using SCA address: %s", self.sca_address)
        self.free_transaction_ids = list(range(1, 255))
        self.transaction = []


    def sendReset(self):
        self.clearCommands()
        txId = self.free_transaction_ids.pop(0)
        self.transaction += self.gbtsca_tx_encode(
            self.broadcast_address,
            self.reply_address,
            0x02, #RESET CMD_ID
            self.sca_address,
            txId,
            0,
            0,
            0
        )
        self.dispatchCommands()


    def sendConnect(self):
        self.clearCommands()
        txId = self.free_transaction_ids.pop(0)
        self.transaction += self.gbtsca_tx_encode(
            self.broadcast_address,
            self.reply_address,
            0x01, #CONNECT CMD_ID
            self.sca_address,
            txId,
            0,
            0,
            0
        )
        self.dispatchCommands()


    def addCommand(self, channel, command, length=1, data=0):
        """
        Add a command to the queue of commands. This method does not *send*
        the command.

        Args:
            channel (int): channel of the GBT-SCA (see table 4.1 in the GBT-SCA
                manual)
            command (int): command code for this channel (typically described
                in the last table of each chapter in the GBT-SCA manual)
            length (int): Length of the payload data in bytes. Default is 1.
            data (int): payload data. Default is 0.

        Raises:
            Exception: if there are no more free transaction IDs.
        """
        if len(self.free_transaction_ids) == 0:
            raise Exception("No more free transaction IDs")
        t_id = self.free_transaction_ids.pop(0)
        self.transaction += self.gbtsca_tx_encode(
                self.broadcast_address, self.reply_address, 0b100,
                self.sca_address, t_id, channel, command, data) 


    def hdlc_reset(self):
        """
        Send an hdlc reset command

        Raises:
            Exception: if there are no more free transaction IDs.
        """
        if len(self.free_transaction_ids) == 0:
            raise Exception("No more free transaction IDs")
        t_id = self.free_transaction_ids.pop(0)
        self.transaction += self.gbtsca_tx_encode(
                self.broadcast_address, self.reply_address, 0b010,
                self.sca_address, 0,0,0,0) 
        self.dispatchCommands()


    def clearCommands(self):
        if not self.transaction:
            self.transaction = []
            return
        decoded_data = self._gbtsca_tx_decode(self.transaction)
        if decoded_data['trans_id']:
            self.free_transaction_ids.append(decoded_data['trans_id'])
        self.transaction = []


    def dispatchCommands(self):
        """
        Send all commands in the queue, and clears the queue.

        Returns:
            A list of replies for all commands.
        """
        self.response = []
        self.sc_interface.message = self.transaction
        self.logger.info("==== Dispatching SCA %d commands ====", len(self.transaction) // 4)
        for i in range(len(self.transaction)//4):
            decoded_data = self._gbtsca_tx_decode(self.transaction[i*4:(i+1)*4])
            self.logger.info("sca >>>> %d: CHANNEL=%s, CMD=%s, transID=%s, payload=%s",
                i,
                sca_transport_tester.channel_to_str(decoded_data['ch_address']),
                sca_transport_tester.cmd_to_str(decoded_data['ch_address'], decoded_data['cmd']),
                decoded_data['trans_id'],
                decoded_data['payload']
            )

        self.received_data, self.number_of_successful_transactions = self.sc_interface.flush()
        self.logger.info("==== Receiving SCA %d data ====", len(self.received_data) // 4)
        for i in range(len(self.received_data) // 4):
            decoded_data = self.gbtsca_rx_decode(
                self.received_data[4*i: 4*(i+1)]
            )
            self.logger.info("sca <<<< %d: CHANNEL=%s, transID=%s, payload=%s, error=%s",
                i,
                sca_transport_tester.channel_to_str(decoded_data['ch_address']),
                decoded_data['trans_id'],
                decoded_data['payload'],
                sca_transport_tester.error_to_str(decoded_data["error"]),
            )
            self.response += [decoded_data]
            if decoded_data['trans_id']:
                self.free_transaction_ids.append(decoded_data['trans_id'])

        self.transaction = []
        return self.response


    def gbtsca_tx_encode(self, bst_address, repl_address, cmd_id, sca_address, trans_id, ch_address, cmd, payload):
        """
        Encodes a transaction to the GBT-SCA into a format that can be used by
        the firmware transactor.
        """
        out = (bst_address &
               gbtsca_tx.BROADCAST_ADDR["MASK"]) << gbtsca_tx.BROADCAST_ADDR["OFFSET"]
        out = out | (
            (repl_address & gbtsca_tx.REPLY_ADDR["MASK"]) << gbtsca_tx.REPLY_ADDR["OFFSET"])
        out = out | (
            (cmd_id & gbtsca_tx.COMMAND_ID["MASK"]) << gbtsca_tx.COMMAND_ID["OFFSET"])
        out = out | (
            (sca_address & gbtsca_tx.SCA_ADDR["MASK"]) << gbtsca_tx.SCA_ADDR["OFFSET"])
        out = out | (
            (trans_id & gbtsca_tx.TRANSACTION_ID["MASK"]) << gbtsca_tx.TRANSACTION_ID["OFFSET"])
        out = out | (
            (ch_address & gbtsca_tx.CHANNEL_ADDR["MASK"]) << gbtsca_tx.CHANNEL_ADDR["OFFSET"])
        out = out | (
            (cmd & gbtsca_tx.COMMAND["MASK"]) << gbtsca_tx.COMMAND["OFFSET"])
        out = out | (
            (payload & gbtsca_tx.PAYLOAD["MASK"]) << gbtsca_tx.PAYLOAD["OFFSET"])

        data = [(out >> i*32) & 0xFFFFFFFF for i in range(4)]

        return data



    def _gbtsca_tx_decode(self, encoded_data):
        """
        Decodes an encoded transaction to the GBT-SCA and returns all
        transaction attributes.
        """
        bst_address = (encoded_data[3] << 8)
        bst_address += (encoded_data[2] >>
                        (gbtsca_tx.BROADCAST_ADDR["OFFSET"] % 32))
        repl_address = (encoded_data[2] >> (
            gbtsca_tx.REPLY_ADDR["OFFSET"] % 32)) & gbtsca_tx.REPLY_ADDR["MASK"]
        cmd_id = (encoded_data[2] >> (
            gbtsca_tx.COMMAND_ID["OFFSET"] % 32)) & gbtsca_tx.COMMAND_ID["MASK"]
        sca_address = (encoded_data[1] >> (
            gbtsca_tx.SCA_ADDR["OFFSET"] % 32)) & gbtsca_tx.SCA_ADDR["MASK"]
        trans_id = (encoded_data[1] >> (
            gbtsca_tx.TRANSACTION_ID["OFFSET"] % 32)) & gbtsca_tx.TRANSACTION_ID["MASK"]
        ch_address = (encoded_data[1] >> (
            gbtsca_tx.CHANNEL_ADDR["OFFSET"] % 32)) & gbtsca_tx.CHANNEL_ADDR["MASK"]
        cmd = (encoded_data[1] >> (gbtsca_tx.COMMAND["OFFSET"] %
               32)) & gbtsca_tx.COMMAND["MASK"]
        payload = encoded_data[0]

        field_dict = {'bst_address': bst_address, 'repl_address': repl_address, 'cmd_id': cmd_id,
                      'sca_address': sca_address, 'trans_id': trans_id, 'ch_address': ch_address,
                      'cmd': cmd, 'payload': payload}

        return field_dict

    def gbtsca_rx_decode(self, data):
        """
        Decodes a reply from the GBT-SCA and returns all the attributes of the
        reply.
        """
        error_flag = ((data[2]) >> (
            gbtsca_rx.ERROR_FLAGS["OFFSET"] % 32)) & gbtsca_rx.ERROR_FLAGS["MASK"]
        sca_address = ((data[2]) >> (
            gbtsca_rx.SCA_ADDR["OFFSET"] % 32)) & gbtsca_rx.SCA_ADDR["MASK"]
        ctrl = ((data[2]) >> (
            gbtsca_rx.CONTROL["OFFSET"] % 32)) & gbtsca_rx.CONTROL["MASK"]
        trans_id = ((data[1]) >> (
            gbtsca_rx.TRANSACTION_ID["OFFSET"] % 32)) & gbtsca_rx.TRANSACTION_ID["MASK"]
        ch_address = ((data[1]) >> (
            gbtsca_rx.CHANNEL_ADDR["OFFSET"] % 32)) & gbtsca_rx.CHANNEL_ADDR["MASK"]
        nbytes = ((data[1]) >> (
            gbtsca_rx.NBYTES_PAYLOAD["OFFSET"] % 32)) & gbtsca_rx.NBYTES_PAYLOAD["MASK"]
        error = (data[1] >> (
            gbtsca_rx.ERROR["OFFSET"] % 32)) & gbtsca_rx.ERROR["MASK"]
        payload = data[0]

        received_dict = {'error_flag': error_flag,
                         'sca_address': sca_address,
                         'ctrl': ctrl,
                         'trans_id': trans_id,
                         'ch_address': ch_address,
                         'nbytes': nbytes,
                         'error': error,
                         'payload': payload
                         }

        return received_dict


    def cmd_id_to_str(cmd_id):
        #lpGBT cmds
        CMDS = [
            "reserved",
            "SCA CONNECT",
            "SCA RESET",
            "reserved",
            "SCA START",
            "reserved",
            "reserved",
            "reserved"
        ]
        return CMDS[cmd_id]

    def channel_to_str(channel):
        #SCA channels
        CHANNELS = {
            0x00: 'CTRL',
            0x01: 'SPI',
            0x02: 'GPIO',
            0x03: 'I2C0',
            0x04: 'I2C1',
            0x05: 'I2C2',
            0x06: 'I2C3',
            0x07: 'I2C4',
            0x08: 'I2C5',
            0x09: 'I2C6',
            0x0A: 'I2C7',
            0x0B: 'I2C8',
            0x0C: 'I2C9',
            0x0D: 'I2CA',
            0x0E: 'I2CB',
            0x0F: 'I2CC',
            0x10: 'I2CD',
            0x11: 'I2CE',
            0x12: 'I2CF',
            0x13: 'JTAG',
            0x14: 'ADC',
            0x15: 'DAC'
        }
        if channel in CHANNELS.keys():
            return CHANNELS[channel]
        return str(channel)


    def cmd_to_str(channel,cmd):
        if sca_transport_tester.channel_to_str(channel)=="CTRL":
            CMDS = {
                0x02: "CTRL_W_CRB",
                0x03: "CTRL_R_CRB",
                0x04: "CTRL_W_CRC",
                0x05: "CTRL_R_CRC",
                0x06: "CTRL_W_CRD",
                0x07: "CTRL_R_CRD",
            }
            if cmd in CMDS.keys():
                return CMDS[cmd]
        elif sca_transport_tester.channel_to_str(channel)=="GPIO":
            CMDS = {
                0x10: "GPIO_W_DATAOUT",
                0x11: "GPIO_R_DATAOUT",
                0x01: "GPIO_R_DATAIN",
                0x20: "GPIO_W_ DIRECTION",
                0x21: "GPIO_R_ DIRECTION",
            }
            if cmd in CMDS.keys():
                return CMDS[cmd]
        elif sca_transport_tester.channel_to_str(channel)=="ADC":
            CMDS = {
                0x02: "ADC_GO",
                0x50: "ADC_W_MUX",
                0x51: "ADC_R_MUX",
                0x60: "ADC_W_CURR",
                0x61: "ADC_R_CURR",
                0x10: "ADC_W_GAIN",
                0x11: "ADC_R_GAIN",
                0x21: "ADC_R_DATA",
                0x31: "ADC_R_RAW",
                0x41: "ADC_R_OFS"
            }
            if cmd in CMDS.keys():
                return CMDS[cmd]
        elif sca_transport_tester.channel_to_str(channel).startswith("I2C"):
            CMDS = {
                0x30: "I2C_W_CTRL",
                0x31: "I2C_R_CTRL",

                0x11: "I2C_R_STR",
                0x20: "I2C_W_MSK",
                0x21: "I2C_R_MSK",

                0x82: "I2C_S_7B_W",
                0x86: "I2C_S_7B_R"
            }
            if cmd in CMDS.keys():
                return CMDS[cmd]
        return str(cmd)


    def error_to_str(error):
        if error==0:
            return "ok"

        ERRORS = {
            0: "Generic",
            1: "Invalid channel",
            2: "Invalid command",
            3: "Invalid transaction number",
            4: "Invalid length",
            5: "Channel not enabled",
            6: "Channel busy",
            7: "Command in treatment"
        }
        result = []
        for i in sorted(ERRORS.keys()):
            if ((error & (1 << i)) >> i) > 0:
                result.append(ERRORS[i])

        return str(result)
