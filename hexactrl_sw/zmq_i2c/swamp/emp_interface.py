import uhal
import emp
from swamp.core import Transport
from swamp.gbtsca_transport import sca_transport

class emp_interface:
    def __init__(self,
                 connectionFile : str = "file:///opt/hgc_utils/etc/connections.xml",
                 deviceName : str = "x0",
                 emp_channel : int = 13,
                 timeout : int = 10000 ):
        self.connections = connectionFile
        self.device = deviceName
        uhal.setLogLevelTo( uhal.LogLevel.ERROR )
        self.hw = uhal.ConnectionManager(self.connections).getDevice(self.device)
        self.empController = emp.Controller(self.hw)
        self.empController.hw().setTimeoutPeriod(timeout)
        self.emp_channel = emp_channel


    def activateEMPChannel(self):
        self.empController.getDatapath().selectRegion(self.emp_channel//4)
        self.empController.getDatapath().selectLink(self.emp_channel)

    def set_EC(self):
        self.activateEMPChannel()
        # enable EC mux
        self.hw.getNode("datapath.region.fe_mgt.data_framer.ctrl.ec_ic").write(1)
        self.hw.dispatch()
    
    def set_IC(self):
        self.activateEMPChannel()
        # disable EC mux
        self.hw.getNode("datapath.region.fe_mgt.data_framer.ctrl.ec_ic").write(0)
        self.hw.dispatch()
    

    def write_IC(self, reg, val, lpgbt_addr=0x70):
        self.empController.getSCC().reset()
        if not (type(val) == list):
            val = [val]
        #print(f"INFO: writeIC :  reg_add = 0x{reg:04x}, val0 = 0x{val[0]:04x}, val_len = {len(val)}, lpgbt_addr = 0x{lpgbt_addr:02x}  ")		
        self.empController.getSCCIC().icWriteBlock(reg, val, lpgbt_addr)


    def read_IC(self, reg, nread=1, lpgbt_addr=0x70):
        #print(f'reg = {hex(reg)}, nread = {nread}')
        self.empController.getSCC().reset()
        words = []
        if nread == 1:
            lReply = self.empController.getSCCIC().icRead(reg, lpgbt_addr)
        else:
            lReply = []
            ## not pretty but we have seen issues when trying to read more registers in 1 icReadBlock call (limit was found for 24 consecutive registers)
            maxNbrRegPerRead=16
            number_of_IC_read = int( (nread-1)/maxNbrRegPerRead )+1
            #print(number_of_IC_read)
            for iread in range(number_of_IC_read):
                reg_addr = reg + iread * maxNbrRegPerRead
                read_len = maxNbrRegPerRead if iread+1<number_of_IC_read else nread%maxNbrRegPerRead if nread%maxNbrRegPerRead>0 else maxNbrRegPerRead
                lReply.extend( self.empController.getSCCIC().icReadBlock(reg_addr, read_len, lpgbt_addr) )        
            #lReply = self.empController.getSCCIC().icReadBlock(reg, nread, lpgbt_addr)
        
        

        if type(lReply) != list:
            lReply = [lReply]

        for word in lReply:
            words.append(word & 0xFF)
            #print(f" DEBUG: readIC : add_base= 0x{reg:02x} lReply = 0x{word:08x}")
        
        return words 


class emp_transport(Transport):
    def __init__(self, name : str="", cfg : dict={} ):
        super().__init__(name=name, cfg=cfg)
        connectionFile = self.cfg['connectionFile'] if 'connectionFile' in cfg  else "file:///opt/hgc_utils/etc/connections.xml"
        deviceName = self.cfg['deviceName'] if 'deviceName' in cfg else 'x0'
        emp_channel = self.cfg['emp_channel'] if 'emp_channel' in cfg else 13
        timeout = self.cfg['timeout'] if 'timeout' in cfg else 10000
        self.transactor = emp_interface(connectionFile=connectionFile,
                                                  deviceName=deviceName,
                                                  emp_channel=emp_channel,
                                                  timeout=timeout)
                
    def setLoggingLevel(self,level):
        super().setLoggingLevel(level)


class sca_transport_emp(sca_transport):
    """
    Implementation of the GBT-SCA transport class for the EMP firmware
    transactor.

    Attributes:
        sca_address (int): Address of the GBT-SCA, inherited from sca_transport
        transactor (emp_interface): Instance of the interface class to EMP
        sca_spare (int): ID of the spare eLink SCA connection. Use -1 to talk
            to the SCA via the lpGBT's EC port.
    """
    def __init__(self, name : str="", cfg : dict={}):
        """
        Args:
            name (str): Name of this SWAMP object
            cfg (str): Configuration dictionary

        Configuration parameters:
            connectionFile (str): Path to the EMP connection file.
            deviceName (str): x0 or x1, the FPGA site on the Serenity.
            emp_channel (int): The EMP channel. Defaults to 13.
            timeout (int): Defaults to 10000
            sca_address (int): Address of the GBT-SCA. Defaults to 0.
            sca_spare (int): ID of the spare eLink SCA connection.
                Defaults to 0.
        """
        super().__init__(name=name, cfg=cfg)

        connectionFile = cfg['connectionFile'] if 'connectionFile' in cfg  else "file:///opt/hgc_utils/etc/connections.xml"
        deviceName = cfg['deviceName'] if 'deviceName' in cfg else 'x0'
        emp_channel = cfg['emp_channel'] if 'emp_channel' in cfg else 13
        timeout = cfg['timeout'] if 'timeout' in cfg else 10000
        self.transactor = emp_interface(connectionFile=connectionFile,
                                                  deviceName=deviceName,
                                                  emp_channel=emp_channel,
                                                  timeout=timeout)

        self.sca_spare = cfg.get("sca_spare", 0)

        self.transactor.activateEMPChannel()
        if self.sca_spare >= 0:
            self.transactor.empController.getSCC().selectECspare(self.sca_spare)
        self.commands = []


    def sendReset(self):
        """
        Send a reset coommand to the front end.
        """
        self.transactor.empController.getSCC().reset()

        if self.sca_spare >= 0:
            return self.transactor.empController.getSCCECspare().sendResetCommand(self.sca_address)
        else:
            return self.transactor.empController.getSCCEC().sendResetCommand(self.sca_address)


    def sendConnect(self):
        """
        Send a connect command to the front end.
        """
        self.transactor.empController.getSCC().reset()

        if self.sca_spare >= 0:
            self.transactor.empController.getSCCECspare().sendConnectCommand(self.sca_address)
        else:
            self.transactor.empController.getSCCEC().sendConnectCommand(self.sca_address)


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
        header = ((0x000000ff & command) << 16) | ((0x000000ff & length) << 8) | ((0x000000ff & channel))
        self.commands.append(header)
        if type(data) is list:
            self.commands.extend(data)
        else:
            self.commands.append(data)


    def clearCommands(self):
        """
        Clear the queue of commands without sending them.
        """
        self.commands.clear()


    def dispatchCommands(self):
        """
        Send all commands in the queue, and clears the queue.

        Returns:
            A list of replies for all commands.
        """
        reply = []

        try:
            # Run the command
            if self.sca_spare >= 0:
                c = self.transactor.empController.getSCCECspare().sendCommandsAndReturnRepliesDirectly(self.commands, self.sca_address)
            else:
                c = self.transactor.empController.getSCCEC().sendCommandsAndReturnRepliesDirectly(self.commands, self.sca_address)

            # Convert the reply to a proper payload list
            for cmd, data in zip(c[::2], c[1::2]):
                reply.append(self.gbtsca_rx_decode(cmd, data))
        except Exception as e:
            self.logger.error("Dispatch {} SCA command(s) -> ERROR: {}".format(
                len(self.commands) // 2, e
            ))

        self.clearCommands()

        return reply


    def gbtsca_rx_decode(self, cmd, data):
        """
        Decodes a reply from the GBT-SCA and returns all the attributes of the
        reply.
        """
        error_flag = 0
        sca_address = self.sca_address
        ctrl = (cmd & 0x00ff0000) >> 16
        trans_id = 0
        ch_address = cmd & 0x000000ff
        nbytes = (cmd & 0x0000ff00) >>  8
        error = 0

        received_dict = {'error_flag': error_flag,
                         'sca_address': sca_address,
                         'ctrl': ctrl,
                         'trans_id': trans_id,
                         'ch_address': ch_address,
                         'nbytes': nbytes,
                         'error': error,
                         'payload': data
                         }

        return received_dict