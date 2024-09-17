import swamp.util as util

# register map : https://gitlab.cern.ch/cms-hgcal-firmware/components/hgcal_slow_control/-/blob/Vivado2019.2/Documentation/SlowControlDocumentation.pdf
BROADCAST_ADDR_OFFSET = 112
BROADCAST_ADDR_MASK = 0xFFFF

REPLY_ADDR_OFFSET = 96
REPLY_ADDR_MASK = 0xF

CHIP_ADDR_OFFSET = 89
CHIP_ADDR_MASK = 0x7F

READ_WRITE_OFFSET = 88
READ_WRITE_MASK = 0x1

REGISTER_ADDR_OFFSET = 72
REGISTER_ADDR_MASK = 0xFFFF

NREG_OFFSET = 64
NREG_MASK = 0xF

PAYLOAD_OFFSET = 0
PAYLOAD_MASK = 0xFFFFFFFFFFFFFFFF

class encoder:    
    def __init__(self,logging_level='INFO'):
        self.logger = util.getLogger("encoder")
        util.setLoggingLevel(logging_level,self.logger)
        self.logger.debug('encoder initialized')

    def setLoggingLevel(self,level):
        util.setLoggingLevel(level,self.logger)

    def encode(self, bst_address, rep_address, chp_address, rw, reg_address, n_reg, payload):
        """
        Arguments:
          bst_address: broadcast address; 16 bits
          rep_address: reply address for command; 4 bits
          chp_address: address of chip to read/write + 1 bit to instruct read or write; 8 bits
          rw         : read/write bit -> 0: write ; 1: read
          reg_address: address of register at which to begin writing; 16 bits
          n_reg      : number of registers to write; up to 8
          payload    : entries to write; between zero and eight bytes
        Output: list of 4 32-bit words
        """

        if payload > PAYLOAD_MASK:
            raise ValueError('Payload is more than {blen(BROADCAST_ADDR_MASK)} bits')

        if n_reg > NREG_MASK:
            raise ValueError('nreg is more than {blen(NREG_MASK)} bits')

        if reg_address > REGISTER_ADDR_MASK:
            raise ValueError('Register address is more than {blen(REGISTER_ADDR_MASK)} bits')

        if chp_address > CHIP_ADDR_MASK:
            raise ValueError('Chip address is more than {blen(CHIP_ADDR_MASK)} bits')

        if rw > READ_WRITE_MASK:
            raise ValueError('Read/Write is more than {blen(CHIP_ADDR_MASK)} bits')

        if rep_address > REPLY_ADDR_MASK:
            raise ValueError('Reply address is more than {blen(REPLY_ADDR_MASK)} bits')

        if bst_address > BROADCAST_ADDR_MASK:
            raise ValueError('Reply address is more than {blen(BROADCAST_ADDR_MASK)} bits')

        out = (bst_address & BROADCAST_ADDR_MASK) << BROADCAST_ADDR_OFFSET
        out = out | ((rep_address & REPLY_ADDR_MASK) << REPLY_ADDR_OFFSET)
        out = out | ((chp_address & CHIP_ADDR_MASK) << CHIP_ADDR_OFFSET)
        out = out | ((rw & READ_WRITE_MASK) << READ_WRITE_OFFSET)
        out = out | ((reg_address & REGISTER_ADDR_MASK) << REGISTER_ADDR_OFFSET)
        out = out | ((n_reg & NREG_MASK) << NREG_OFFSET)
        out = out | ((payload & PAYLOAD_MASK) << PAYLOAD_OFFSET)

        data = [ (out>>i*32)&0xFFFFFFFF for i in range(4)]

        self.logger.debug( f'encoding bst_address={hex(bst_address)}, rep_address={hex(rep_address)}, chp_address={hex(chp_address)}, rw={hex(rw)}, reg_address={hex(reg_address)}, n_reg={hex(n_reg)}, payload={hex(payload)}' )
        self.logger.debug( f'returns {hex(data[0])} {hex(data[1])} {hex(data[2])} {hex(data[3])}' )
        return data
        
    def decode(self, encoded_data):
        """
          encoded_data: list of 4 32-bits words
          only needed for debugging purpose (i think)
        """
        if len(encoded_data) != 4:
            raise ValueError('encoded data should be a list of 4 32-bits words')
        bit_lenght_error = [ util.blen(d)>32 for d in encoded_data ]
        if True in bit_lenght_error:
            raise ValueError('at least 1 word in encoded data is more than 32-bits')
            
        # parse fields
        bst_address = ( (encoded_data[3]) >> (BROADCAST_ADDR_OFFSET % 32) ) & BROADCAST_ADDR_MASK
        rep_address = ( (encoded_data[3]) >> (REPLY_ADDR_OFFSET % 32) )     & REPLY_ADDR_MASK
        chp_address = ( (encoded_data[2]) >> (CHIP_ADDR_OFFSET % 32) )      & CHIP_ADDR_MASK
        rw          = ( (encoded_data[2]) >> (READ_WRITE_OFFSET % 32) )     & READ_WRITE_MASK
        reg_address = ( (encoded_data[2]) >> (REGISTER_ADDR_OFFSET % 32) )  & REGISTER_ADDR_MASK
        n_reg       = ( (encoded_data[2]) >> (NREG_OFFSET % 32) )           & NREG_MASK
        payload     = (encoded_data[1]>>32) | (encoded_data[0])

        retdict = {'bst_address': bst_address, 'rep_address': rep_address, 'chp_address': chp_address,
                   'rw': rw, 'reg_address': reg_address, 'n_reg': n_reg, 'payload': payload}

        self.logger.debug( f'decoding: {encoded_data}' )
        self.logger.debug( f'returns {retdict}' )

        return retdict
