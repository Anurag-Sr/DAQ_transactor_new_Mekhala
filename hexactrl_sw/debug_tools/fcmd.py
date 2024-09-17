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


    #dev.getNode("fastcontrol.command.enable_periodic_l1a_A").write(0x0)
    #dev.getNode("fastcontrol.command.enable_periodic_l1a_B").write(0x0)
    #dev.getNode("fastcontrol.command.enable_periodic_l1a_C").write(0x0)
    #dev.getNode("fastcontrol.command.enable_periodic_l1a_D").write(0x0)
    #dev.getNode("fastcontrol.command.enable_random_l1a").write(0x0)
    #dev.getNode("fastcontrol.command.enable_periodic_ancillary").write(0x0)


    #dev.getNode("fastcontrol.l1aperiodic_A.bx").write(10)
    #dev.getNode("fastcontrol.l1aperiodic_A.orbit_prescale").write(0x0)
    #dev.getNode("fastcontrol.channel_A_settings.type").write(0)
    #dev.getNode("fastcontrol.channel_A_settings.length").write(1)
    #dev.getNode("fastcontrol.channel_A_settings.follow_mode_enable").write(0)

    #dev.getNode("fastcontrol.l1aperiodic_B.bx").write(14)
    #dev.getNode("fastcontrol.l1aperiodic_B.orbit_prescale").write(0x0)
    #dev.getNode("fastcontrol.channel_B_settings.type").write(2)
    #dev.getNode("fastcontrol.channel_B_settings.length").write(1)
    #dev.getNode("fastcontrol.channel_B_settings.follow_mode_enable").write(0)

    #dev.getNode("fastcontrol.l1aperiodic_C.bx").write(18)
    #dev.getNode("fastcontrol.l1aperiodic_C.orbit_prescale").write(0x0)
    #dev.getNode("fastcontrol.channel_C_settings.type").write(0)
    #dev.getNode("fastcontrol.channel_C_settings.length").write(1)
    #dev.getNode("fastcontrol.channel_C_settings.follow_mode_enable").write(0)

    #dev.getNode("fastcontrol.l1aperiodic_D.bx").write(22)
    #dev.getNode("fastcontrol.l1aperiodic_D.orbit_prescale").write(0x0)
    #dev.getNode("fastcontrol.channel_D_settings.type").write(0)
    #dev.getNode("fastcontrol.channel_D_settings.length").write(1)
    #dev.getNode("fastcontrol.channel_D_settings.follow_mode_enable").write(0)

    #dev.getNode("fastcontrol.ancillary_settings.bx").write(0x100)
    #dev.getNode("fastcontrol.ancillary_settings.orbit_prescale").write(0x0)
    #dev.getNode("fastcontrol.ancillary_settings.length").write(0x0)


    dev.getNode("fastcontrol.periodic0.enable").write(0x1)
    dev.getNode("fastcontrol.periodic0.bx").write(0xa)
    dev.getNode("fastcontrol.periodic0.flavor").write(0x0)
    dev.getNode("fastcontrol.command.global_l1a_enable").write(0x0)
    dev.getNode("fastcontrol.command.prel1a_offset").write(0x1)
    dev.getNode("fastcontrol.command.global_l1a_enable").write(0x1)
