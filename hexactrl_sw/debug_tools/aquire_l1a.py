##
# please run me from the hexactrl-sw directory:
# python debug_tools/aquire_l1a.py -c 0 -l daq1 -s 100 -o 14
##
import os
from optparse import OptionParser
        
def get_comma_separated_args(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option('-l', '--links', dest="links",action="callback",type=str,
                      help="links name to align", callback=get_comma_separated_args, default=[])
    parser.add_option("-L", "--logLevel", dest="logLevel",type=int,action="store",
                      help="log level which will be applied to all cmd",default=0)
    parser.add_option("-n", "--nevent", dest="nevent",type=int,action="store",
                      help="number of event per burst (only one burst will be sent), maximum nevent = 95",default=1)
    parser.add_option("-s", "--bsise", dest="bsize",type=int,action="store",
                      help="size (in unit of 32 bit words) of bram to print out",default=1000)
    parser.add_option("-o", "--offset_l1a", dest="l1aoffset",type=int,action="store",
                      help="offset from BRAM write start in 40 MHz clock ticks in L1A capture mode, or BX count to trigger BX capture mode",default=-1)
    parser.add_option("-g", "--l1agen", dest="l1agen",action="store",
                      help="type of L1A generator : options : A, B, AB",default="A")
    parser.add_option("-a", "--BX_A", dest="BX_A",type=int,action="store",
                      help="bunch crossing id for l1As of type A",default=10)
    parser.add_option("-b", "--BX_B", dest="BX_B",type=int,action="store",
                      help="bunch crossing id for l1As of type B",default=1000)
    parser.add_option("-i", "--BX_Req", dest="BX_Req",type=int,action="store",
                      help="bunch crossing id for calibration request",default=10)
    parser.add_option("-I", "--BX_InjL1A", dest="BX_InjL1A",type=int,action="store",
                      help="bunch crossing id for calibration l1As after calibration request ",default=20)

    (options, args) = parser.parse_args()

    base_cmd = "./bin/ipbus-ctrl -f address_table/connection.xml -d mylittlememory -L " + str(options.logLevel)+" "
    
    #configure the link

    cmd = base_cmd + "-n fastcontrol.command.enable_orbit_sync -w 1 -D 1"
    print(cmd)
    os.system(cmd)

    cmd = base_cmd + "-n fastcontrol.bx_A.l1a -w 1 -D "+str(options.BX_A)
    print(cmd)
    os.system(cmd)
    cmd = base_cmd + "-n fastcontrol.bx_B.l1a -w 1 -D "+str(options.BX_B)
    print(cmd)
    os.system(cmd)
    
    cmd = base_cmd + "-n fastcontrol.command.enable_periodic_l1a_A -w 1 -D 0"
    os.system(cmd)
    cmd = base_cmd + "-n fastcontrol.command.enable_periodic_l1a_B -w 1 -D 0"
    os.system(cmd)
    cmd = base_cmd + "-n fastcontrol.command.enable_per_calib_req -w 1 -D 0"
    os.system(cmd)
    cmd = base_cmd + "-n fastcontrol.command.enable_calib_l1a -w 1 -D 0"
    os.system(cmd)
    
    if options.l1agen=="AB":
        cmd = base_cmd + "-n fastcontrol.command.enable_periodic_l1a_A -w 1 -D 1"
        print(cmd)
        os.system(cmd)
        cmd = base_cmd + "-n fastcontrol.command.enable_periodic_l1a_B -w 1 -D 1"
        print(cmd)
        os.system(cmd)
    elif options.l1agen=="A":
        cmd = base_cmd + "-n fastcontrol.command.enable_periodic_l1a_A -w 1 -D 1"
        print(cmd)
        os.system(cmd)
    elif options.l1agen=="B":
        cmd = base_cmd + "-n fastcontrol.command.enable_periodic_l1a_B -w 1 -D 1"
        print(cmd)
        os.system(cmd)
    elif options.l1agen=="calib":
        cmd = base_cmd + "-n fastcontrol.command.enable_per_calib_req -w 1 -D 1"
        print(cmd)
        os.system(cmd)
        cmd = base_cmd + "-n fastcontrol.command.enable_calib_l1a -w 1 -D 1"
        print(cmd)
        os.system(cmd)
        cmd = base_cmd + "-n fastcontrol.bx_calib.l1a_notcalib -w 1 -D 1"
        print(cmd)
        os.system(cmd)
    
    nevent = options.nevent
    if nevent>95:
        nevent95

    link_capture_name="link_capture_daq"
    bram_name="bram_daq"

    for link in options.links:

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".capture_mode_in -w 1 -D 2"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".aquire_length -w 1 -D 43"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".total_length -w 1 -D "+str(43*nevent)
        print(cmd)
        os.system(cmd)
        
        if options.l1aoffset>0:
            cmd = base_cmd + "-n "+link_capture_name+"."+link+".L1A_offset_or_BX -w 1 -D "+str(options.l1aoffset)
            print(cmd)
            os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".aquire -w 1 -D 1"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+link_capture_name+"."+link+".aquire -w 1 -D 0"
        print(cmd)
        os.system(cmd)

        cmd = base_cmd + "-n "+bram_name+"."+link+" -s "+str(options.bsize)
        print(cmd)
        os.system(cmd)

