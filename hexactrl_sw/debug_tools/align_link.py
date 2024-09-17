##
# please run me from the hexactrl-sw directory:
# python debug_tools/align_link.py -t daq -l link0,link1 -d 100 -s 50
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
    parser.add_option("-d", "--idelay", dest="idelay",type=int,action="store",
                      help="idelay setting to set for the alignment",default=1)
    parser.add_option("-i", "--invert_pol", dest="invert_pol",type=int,action="store",
                      help="set to 1 to invert the link polarity",default=0)
    parser.add_option("-s", "--bsise", dest="bsize",type=int,action="store",
                       help="size (in unit of 32 bit words) of bram to print out",default=1000)

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

    triglink=False
    link_capture_name="link_capture_daq"
    bram_name="bram_daq"
    if options.linktype.find('trg')==0 :
        triglink=True
        link_capture_name="link_capture_trg"
        bram_name="bram_trg"

    for link in options.links:
        dev.getNode(link_capture_name+"."+link+".explicit_resetb").write(0x0)
        dev.getNode(link_capture_name+"."+link+".explicit_resetb").write(0x1)

        dev.getNode(link_capture_name+"."+link+".delay.in").write(options.idelay)
        dev.getNode(link_capture_name+"."+link+".delay.set").write(0x0)
        dev.getNode(link_capture_name+"."+link+".delay.set").write(0x1)
        if options.invert_pol==1:
            dev.getNode(link_capture_name+"."+link+".delay.invert").write(0x1)
        else:
            dev.getNode(link_capture_name+"."+link+".delay.invert").write(0x0)
        dev.getNode(link_capture_name+"."+link+".capture_mode_in").write(0x0)

        if not triglink :
            dev.getNode(link_capture_name+"."+link+".aquire_length").write(0x1000)
        else:
            dev.getNode(link_capture_name+"."+link+".aquire_length").write(0x200)

        dev.getNode(link_capture_name+"."+link+".explicit_align").write(0x1)
        dev.getNode("fastcontrol.request.link_reset_roct").write(0x1)                                                                            
        dev.getNode("fastcontrol.request.link_reset_rocd").write(0x1) 
        dev.getNode(link_capture_name+"."+link+".explicit_align").write(0x0)


    for link in options.links:
        success = dev.getNode(link_capture_name+"."+link+".link_aligned_count").read()
        errors  = dev.getNode(link_capture_name+"."+link+".link_error_count").read()
        aligned = dev.getNode(link_capture_name+"."+link+".status.link_aligned").read()
        dev.dispatch()
        print("link: %s; nsuccess = %d;  nerrors = %d; aligned = %d"%(link,success,errors,aligned))
        dev.getNode(link_capture_name+".global.interrupt_enable."+link).write(0x1)
        dev.getNode(link_capture_name+"."+link+".aquire").write(0x1)


    interrupts = dev.getNode(link_capture_name+".global.interrupt_vec").read()
    dev.dispatch()
    print("ninterrupts = %d"%(interrupts))
    
    
    for link in options.links:
        data = dev.getNode(bram_name+"."+link).readBlock(options.bsize)
        dev.dispatch()
        print([hex(i) for i in data])
        dev.getNode(link_capture_name+"."+link+".aquire").write(0x0)
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x0)
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x1)
    dev.getNode(link_capture_name+".global.interrupt_enable").write(0x0)

