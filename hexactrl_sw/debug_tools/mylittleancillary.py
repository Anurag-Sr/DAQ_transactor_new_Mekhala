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
    parser.add_option("-b", "--bx", dest="bx",action="store",type=int,
                      help="bx of ancillary trigger",default=0x10)
    parser.add_option('-p', '--prescale', dest="prescale",type=int,action="store",
                      help="orbit prescale for ancillary trigger", default=0)
    parser.add_option('-l', '--length', dest="length",type=int,action="store",
                      help="length of ancillary trigger (in unit of BX)", default=500)
    parser.add_option('-e', '--enable', dest="enable",action="store_true",
                      help="boolean to enable/disbale ancillary trigger", default=False)
    parser.add_option("-L", "--logLevel", dest="logLevel",action="store",
                      help="log level which will be applied to all cmd : ERROR, WARNING, DEBUG, INFO, NOTICE",default="NOTICE")

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

    dev.getNode("fastcontrol.command.enable_orbit_sync").write(0x1)

    dev.getNode("fastcontrol.ancillary_settings.bx").write(options.bx)
    dev.getNode("fastcontrol.ancillary_settings.orbit_prescale").write(options.prescale)
    dev.getNode("fastcontrol.ancillary_settings.length").write(options.length)

    bx=dev.getNode("fastcontrol.ancillary_settings.bx").read()
    prescale=dev.getNode("fastcontrol.ancillary_settings.orbit_prescale").read()
    length=dev.getNode("fastcontrol.ancillary_settings.length").read()
    dev.dispatch()
    print( "ancillary trigger bx, prescale, length : %d, %d, %d"%(bx,prescale,length))

    if options.enable==True:
        dev.getNode("fastcontrol.command.enable_periodic_ancillary").write(0x1)
    else:
        dev.getNode("fastcontrol.command.enable_periodic_ancillary").write(0x0)

