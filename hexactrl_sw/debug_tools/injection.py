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
    parser.add_option("-t", "--linktype", dest="linktype",action="store",
                      help="type of link to align : daq or trig",default="daq")
    parser.add_option('-l', '--links', dest="links",action="callback",type=str,
                      help="links name to align : link0, link1, ..., link11", callback=get_comma_separated_args, default=[])
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

    # print(" dev.getNode(\"fastcontrol.command.enable_orbit_sync\").write(0x1) ")                   
    dev.getNode("fastcontrol.command.enable_orbit_sync").write(0x1)

    bsize = dev.getNode("fastcontrol.bx_orbit_sync").read()
    dev.dispatch()

    triglink=False
    link_capture_name="link_capture_daq"
    bram_name="bram_daq"
    if options.linktype.find('trg')==0 :
        triglink=True
        link_capture_name="link_capture_trg"
        bram_name="bram_trg"

    dev.getNode(link_capture_name+".global.interrupt_enable").write(0x0)
    
    event_per_burst = dev.getNode(link_capture_name+".global.bram_size").read()
    dev.dispatch()
    event_per_burst = int(event_per_burst)/(43*3)

    for link in options.links:
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x0);
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x1);
        dev.getNode(link_capture_name+"."+link+".capture_mode_in").write(0x2);
        dev.getNode(link_capture_name+"."+link+".aquire_length").write(43);
        dev.getNode(link_capture_name+"."+link+".total_length").write(43*event_per_burst);
        dev.getNode(link_capture_name+".global.interrupt_enable."+link).write(0x1)

    dev.getNode("fastcontrol.bx_calib.req").write(0x10)
    dev.getNode("fastcontrol.bx_calib.l1a").write(0x10+20)
    dev.getNode("fastcontrol.bx_calib.l1a_notcalib").write(0x1)
    
    for link in options.links:
        dev.getNode(link_capture_name+".global.continous_acquire."+link).write(0x1);

    dev.getNode("fastcontrol.command.enable_calib_l1a").write(0x1)
                
    interrupts = dev.getNode(link_capture_name+".global.interrupt_vec").read()
    dev.dispatch()

    for link in options.links:
        data = dev.getNode(bram_name+"."+link).readBlock(43*event_per_burst)
        dev.dispatch()
        # print( [hex(i) for i in data] )
        bx = [ (data[i*43]>>12)&0xfff for i in range(event_per_burst) ]
        print( bx )

    dev.getNode("fastcontrol.command.enable_calib_l1a").write(0x0)

    for link in options.links:
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x0);
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x1);
    dev.getNode(link_capture_name+".global.interrupt_enable").write(0x0)

