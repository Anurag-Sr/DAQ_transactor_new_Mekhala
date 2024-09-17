import swamp.util as util

# register map : https://gitlab.cern.ch/cms-hgcal-firmware/components/hgcal_slow_control/-/blob/Vivado2019.2/Documentation/SlowControlDocumentation.pdf
ERROR_FLAGS_OFFSET = 125
ERROR_FLAGS_MASK = 0x7

CHIP_ADDR_OFFSET = 113
CHIP_ADDR_MASK = 0x7F

READ_WRITE_OFFSET = 112
READ_WRITE_MASK = 0x1

LPGBT_COMMAND_OFFSET = 105
LPGBT_COMMAND_MASK = 0x7F

PARITY_FLAG_OFFSET = 104
PARITY_FLAG_MASK = 0x1

NREG_OFFSET = 88
NREG_MASK = 0xF

REGISTER_ADDR_OFFSET = 72
REGISTER_ADDR_MASK = 0xFFFF

PARITY_WORD_OFFSET = 64
PARITY_WORD_MASK = 0xFF

# # not used
# PAYLOAD_OFFSET = 0
# PAYLOAD_MASK = 0xFFFFFFFFFFFFFFFF

class decoder:    
    def __init__(self,logging_level='INFO'):
        self.logger = util.getLogger("decoder")
        util.setLoggingLevel(logging_level,self.logger)
        self.logger.debug('decoder initialized')
        
    def setLoggingLevel(self,level):
        util.setLoggingLevel(level,self.logger)

    def decode(self, encoded_data):
        """
          encoded_data: list of 4 32-bits words
        """
        if len(encoded_data) != 4:
            raise ValueError('encoded data should be a list of 4 32-bits words')
        bit_lenght_error = [ util.blen(d)>32 for d in encoded_data ]
        if True in bit_lenght_error:
            raise ValueError('at least 1 word in encoded data is more than 32-bits')
            
        # parse fields
        error_flag    = ( (encoded_data[3]) >> (ERROR_FLAGS_OFFSET % 32) )    & ERROR_FLAGS_MASK
        chp_address   = ( (encoded_data[3]) >> (CHIP_ADDR_OFFSET % 32) )      & CHIP_ADDR_MASK
        rw            = ( (encoded_data[3]) >> (READ_WRITE_OFFSET % 32) )     & READ_WRITE_MASK
        lpgbt_command = ( (encoded_data[3]) >> (LPGBT_COMMAND_OFFSET % 32) )  & LPGBT_COMMAND_MASK
        parity_flag   = ( (encoded_data[3]) >> (PARITY_FLAG_OFFSET % 32) )    & PARITY_FLAG_MASK
        n_reg         = ( (encoded_data[2]) >> (NREG_OFFSET % 32) )           & NREG_MASK
        reg_address   = ( (encoded_data[2]) >> (REGISTER_ADDR_OFFSET % 32) )  & REGISTER_ADDR_MASK
        parity_word   = ( (encoded_data[2]) >> (PARITY_WORD_OFFSET % 32) )    & PARITY_WORD_MASK
        payload       = (encoded_data[1]<<32) | (encoded_data[0])

        retdict = { 'error_flag': error_flag, 
                    'chp_address': chp_address,
                    'rw': rw,
                    'lpgbt_command' : lpgbt_command,
                    'parity_flag' : parity_flag,
                    'n_reg': n_reg,
                    'reg_address': reg_address,
                    'parity_word': parity_word,
                    'payload': payload
        }

        self.logger.debug( f'decoding: {encoded_data}' )
        self.logger.debug( f'returns {retdict}' )

        return retdict
