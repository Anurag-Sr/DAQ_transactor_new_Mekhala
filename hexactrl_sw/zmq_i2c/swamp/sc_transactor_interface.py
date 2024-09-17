import uhal
import logging
from swamp.util import *
    
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class sc_transactor_interface(metaclass=Singleton):
    """
    Class which reads and writes via the optical link. It is agnostic to the protocol with which to write,
    though it does expect 128-bit command strings formatted into a list of four blocks of 32 bits each. An
    encoder class might format the commands properly and then pass them to this class to send and receive. 
    """
    
    def __init__(self, 
                 connection_file : str='file:///opt/hgc_utils/etc/connections.xml', 
                 device_name : str='x1'):
        """
        Initializer
        see https://gitlab.cern.ch/hgc-daq-demo/slow_control_demo/-/blob/Vivado2019.2/LinuxTestSW/testSlowControl.py
        for source of the initializing code
        """
        # self.logger = logging.getLogger('sc_transactor_interface')

        uhal.setLogLevelTo(uhal.LogLevel.WARNING)    
        self.man = uhal.ConnectionManager(connection_file)
        print(self.man.getDevices())
        self.dev = self.man.getDevice(device_name)

        self.ResetSlowControl()
        # self.lpGBTResetRX()
        # self.lpGBTReadReady()

    # def setLoggingLevel(self, level):
    #     util.setLoggingLevel(level, self.logger)

    def send_recv(self, data):
        """
        Combines send and recv functions, each of which are below. The "data" input should be a list
        of blocks, where each command is a sequence of four blocks. Hence, the length of data should be
        divisible by 4 (which is verified in the send function). 
        data: blocks to send
        returns: list of received blocks; same length as data
        """
        
        # self.logger.debug('Received send and receive command')

        self.send(data)
        return self.recv(int(len(data)/4))

    def send(self, data):
        """
        Sends command to lpGBT. Expects list of 32-bit blocks, with the length of the list divisible by
        four. Both qualities are verified.
        data: blocks to send
        """
        
        # self.logger.debug('Received command to write data: '+str([hexb(d, 8) for d in data]))

        if len(data) % 4 != 0:
            raise ValueError('Data must be list with 4*i blocks')

        for block in data:
            if blen(block) > 32:
                raise ValueError('Data blocks cannot be larger than 32-bit/8-hex')

        nbr_transactions = int(len(data)/4)

        # self.logger.debug('Writing '+str(nbr_transactions)+' transactions')

        self.dev.getNode("slow_control_data.IC_TX_BRAM0.Data").writeBlock(data)
        self.dev.getNode("slow_control_config.IC_Control0.NbrTransactions").write(nbr_transactions)
        self.dev.getNode("slow_control_config.IC_Control0.Start").write(0x1)
        self.dev.getNode("slow_control_config.IC_Control0.Start").write(0x0)

    def recv(self, nbr_transactions):
        """
        Receive command from lpGBT. Listens to lpGBT output for the expected number of transactions, and 
        returns them as a list.
        nbr_transactions: number of transactions to listen for and return
        """

        # self.logger.debug('Received command to read '+str(nbr_transactions)+' transactions')

        while True:
            if self.dev.getNode("slow_control_config.IC_Status0.Busy").read() == 0:
                break
        data = self.dev.getNode("slow_control_data.IC_RX_BRAM0.Data").readBlock(nbr_transactions*4)

        # self.logger.debug('Read data: '+str([hexb(d, 8) for d in data]))
        return data

    # helper functions
    def lpGBTReadReady(self):
        data = self.dev.getNode("lpGBT_GPIO.Ready").read()
        if data == 0x0:
            print("Neither RX or TX ready")
        elif data == 0x1:
            print("Only RX ready")
        elif data == 0x2:
            print("Only TX ready")
        elif data == 0x3:
            print("Both RX and TX ready")
        else:
            print("Unexpected behaviour\n")

    def get_comma_separated_args(self, option, opt, value, parser):
        setattr(parser.values, option.dest, value.split(','))

    def ResetSlowControl(self):
        self.dev.getNode("slow_control_config.ResetN.rstn").write(0x0)
        self.dev.getNode("slow_control_config.ResetN.rstn").write(0x1)

    def lpGBTResetRX(self):
        self.dev.getNode("lpGBT_GPIO.ResetRX").write(0x1)
        self.dev.getNode("lpGBT_GPIO.ResetRX").write(0x0)
