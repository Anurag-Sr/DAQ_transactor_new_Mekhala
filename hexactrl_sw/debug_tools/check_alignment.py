##
# please run me from the hexactrl-sw directory:
# python debug_tools/check_alignment.py -c 0 -l daq1 -s 100
##
import os
from optparse import OptionParser
        
def get_comma_separated_args(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-t", "--linktype", dest="linktype",action="store",
                      help="type of link to align : daq or trig",default=0)
    parser.add_option('-l', '--links', dest="links",action="callback",type=str,
                      help="links name to align : link0, link1, ..., link11", callback=get_comma_separated_args, default=[])
    parser.add_option("-L", "--logLevel", dest="logLevel",type=int,action="store",
                      help="log level which will be applied to all cmd",default=0)
    parser.add_option("-s", "--bsise", dest="bsize",type=int,action="store",
                      help="size (in unit of 32 bit words) of bram to print out",default=1000)

    (options, args) = parser.parse_args()

    base_cmd = "./bin/ipbus-ctrl -f address_table/connection.xml -d mylittlememory -L " + str(options.logLevel)+" "
    
    #configure the link

    cmd = base_cmd + "-n fastcontrol.command.enable_orbit_sync -w 1 -D 1"
    print(cmd)
    os.system(cmd)

    triglink=False
    link_capture_name="link_capture_daq"
    bram_name="bram_daq"
    if options.linktype.find('trg')==0 :
        triglink=True
        link_capture_name="link_capture_trg"
        bram_name="bram_trg"

    for link in options.links:
        cmd = base_cmd + "-n "+link_capture_name+"."+link+".link_aligned_count"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".link_error_count"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".status.link_aligned"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+".global.interrupt_enable -w 1 -D 0xfff" 
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".aquire -w 1 -D 1"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+".global.interrupt_vec"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+bram_name+"."+link+" -s "+str(options.bsize)
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+".global.interrupt_enable -w 1 -D 0x0" 
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".aquire -w 1 -D 0"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".explicit_rstb_acquire -w 1 -D 0"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".explicit_rstb_acquire -w 1 -D 1"
        print(cmd)
        os.system(cmd)


