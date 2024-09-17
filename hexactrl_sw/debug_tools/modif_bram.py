##
# please run me from the hexactrl-sw directory
# python debug_tools/modif_bram.py -c 0 -l daq0 -s 100
##
import os
from optparse import OptionParser
        
def get_comma_separated_args(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-c", "--chip", dest="chip",action="store",type=int,
                      help="chip ID, it defines the link_capture block ID and the bram controller id",default=0)
    parser.add_option('-l', '--links', dest="links",action="callback",type=str,
                      help="links name to align", callback=get_comma_separated_args, default=[])
    # parser.add_option('-e','--dataNotSaved',dest="dataNotSaved",action="store_true",default=False,
    #                   help="set to true if you don't want to save the data (and the yaml file)")
    parser.add_option("-L", "--logLevel", dest="logLevel",type=int,action="store",
                      help="log level which will be applied to all cmd",default=0)

    parser.add_option("-D", "--dataVal", dest="dataVal",type=str,action="store",
                      help="value which will be set to all words in the selected bram, WARNING: only first byte of the 32-bit words will be modified!!!",default="0xfe")
    parser.add_option("-s", "--bsise", dest="bsize",type=int,action="store",
                      help="size (in unit of 32 bit words) of bram to print out",default=1000)

    (options, args) = parser.parse_args()

    base_cmd = "./bin/ipbus-ctrl -f address_table/connection.xml -d mylittlememory -L " + str(options.logLevel)+" "
    
    #configure the link

    for link in options.links:
        cmd = base_cmd + "-n axi_bram_ctrl_"+str(options.chip)+"."+link+" -w 1 -D "+options.dataVal
        print(cmd)
        os.system(cmd)
        
        cmd = base_cmd + "-n axi_bram_ctrl_"+str(options.chip)+"."+link+" -s "+str(options.bsize)
        print(cmd)
        os.system(cmd)

