##
# please run me from the hexactrl-sw directory:                                                          
# python debug_tools/align_link.py -c 0 -l daq1 -d 16                                                    
##                                                                                                       
import os
from optparse import OptionParser
import uhal

def get_comma_separated_args(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-L", "--logLevel", dest="logLevel",action="store",
                      help="log level which will be applied to all cmd : ERROR, WARNING, DEBUG, INFO, NOTICE",default="NOTICE")

    parser.add_option("-s", "--start", dest="start",action="store_true",
                      help="set to start the self trigger operation")

    (options, args) = parser.parse_args()
    print(options)

    if options.logLevel.find("ERROR")==0:
        uhal.setLogLevelTo(uhal.LogLevel.ERROR)
    elif options.logLevel.find("WARNING")==0:
        uhal.setLogLevelTo(uhal.LogLevel.WARNING)
    elif options.logLevel.find("NOTICE")==0:
        uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    elif options.logLevel.find("DEBUG")==0:
        uhal.setLogLevelTo(uhal.LogLevel.DEBUG)
    elif options.logLevel.find("INFO")==0:
        uhal.setLogLevelTo(uhal.LogLevel.INFO)


    man = uhal.ConnectionManager("file://address_table/connection.xml")
    dev = man.getDevice("mylittlememory")
    
    for i in range(39):
        asum = dev.getNode("mars_accumulator.Sum%d"%(i)).read()
        asum2 = dev.getNode("mars_accumulator.Mult%d"%(i)).read()

        dev.dispatch()
        
        asum2 = (asum & 0xc0000000 << 2) | asum2
        asum = asum & 0x3fffff
        print("Channel %d;\t Sum = %d;\t Sum2 %d"%(i,asum,asum2))
