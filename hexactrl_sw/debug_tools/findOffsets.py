##                                                                                                       
# please run me from the hexactrl-sw directory:                                                          
# python debug_tools/findOffsets.py -t daq -l link0,link1                                                   
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
    for link in options.links:
        dev.getNode(link_capture_name+"."+link+".L1A_offset_or_BX").write(0x0);
        dev.getNode(link_capture_name+"."+link+".fifo_latency").write(0x0);
        dev.getNode(link_capture_name+"."+link+".capture_mode_in").write(0x1);
        dev.getNode(link_capture_name+"."+link+".aquire_length").write(int(bsize));
        dev.getNode(link_capture_name+"."+link+".total_length").write(int(bsize));
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x0);
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x1);
        dev.getNode(link_capture_name+".global.interrupt_enable."+link).write(0x1)

    
    dev.getNode("fastcontrol.command.global_l1a_enable").write(0x0)
    dev.getNode(link_capture_name+".global.aquire").write(0x1);
    interrupts = dev.getNode(link_capture_name+".global.interrupt_vec").read()
    for link in options.links:
        dev.getNode(link_capture_name+"."+link+".aquire").write(0x1);
        data = dev.getNode(bram_name+"."+link).readBlock(int(bsize))
        hexd = [hex(i) for i in data]
	#print(hexd)
        try:
            index = next( i for i,v in enumerate(data) if v & 0xf0000000 == 0x90000000 )
            print("index = %d"%index)
        except (StopIteration):
            print("fifo latency not found")

        dev.getNode(link_capture_name+"."+link+".aquire").write(0x0)
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x0)
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x1)
        dev.getNode(link_capture_name+"."+link+".capture_mode_in").write(0x2);
        #dev.getNode(link_capture_name+"."+link+".L1A_offset_or_BX").write(0xa);

    dev.getNode("fastcontrol.periodic0.flavor").write(0x0)
    dev.getNode("fastcontrol.periodic0.bx").write(0xa)
    dev.getNode("fastcontrol.periodic0.enable").write(0x1)
    for link in options.links:
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x0);
        dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x1);
    dev.getNode(link_capture_name+".global.aquire").write(0x1);
    dev.getNode("fastcontrol.command.prel1a_offset").write(0x1)
    dev.getNode("fastcontrol.command.global_l1a_enable").write(0x1)
    interrupts = dev.getNode(link_capture_name+".global.interrupt_vec").read()

    for link in options.links:
        data = dev.getNode(bram_name+"."+link).readBlock(int(bsize))
        try:
            index = next( i for i,v in enumerate(data) if v & 0xf000000f == 0x50000005 )
            print("L1A_offset_or_BX = %d"%index)
        except (StopIteration):
            print("L1A_offset_or_BX latency not found")
        dev.getNode(link_capture_name+"."+link+".L1A_offset_or_BX").write(index);
        


    fccommand = dev.getNode("fastcontrol.command").read()
    dev.dispatch()
    print(bin(int(fccommand)))
    dev.getNode("fastcontrol.command.global_l1a_enable").write(0x0)
    dev.getNode("fastcontrol.periodic0.enable").write(0x0)
    dev.getNode(link_capture_name+".global.aquire").write(0x0);
    for link in options.links:
       dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x0);
       dev.getNode(link_capture_name+"."+link+".explicit_rstb_acquire").write(0x1);
    dev.getNode(link_capture_name+".global.interrupt_enable").write(0x0)
