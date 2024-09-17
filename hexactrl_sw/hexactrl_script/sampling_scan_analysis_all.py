import zmq, datetime,  os, subprocess, sys, yaml, glob
from time import sleep
from nested_dict import nested_dict

import sampling_scan_all as all_samp
import miscellaneous_functions as misc_func
#import analysis.level0.sampling_scan_analysis as analyzer
import zmq_controler as zmqctrl

if __name__ == "__main__":
    parser = misc_func.options_sampling_scan_analyze()
    parser.add_option("--cfgF",default="./configs/init.yaml", action="store", dest="cfgF", help="initial configuration yaml file")
    (options, args) = parser.parse_args()
    print(options)
    (daqsocket,clisocket,i2csocket) = zmqctrl.pre_init(options)

    #injectedChannels = [9, 10, 12, 28, 29, 30, 36, 37, 38, 59]    
    injectedChannels = [0, 2, 4, 6, 8, 10, 12, 14, 16]
    #injectedChannels = [6, 10, 45, 52, 8, 12, 14, 16]    
    all_samp.Sampling_scan_analysis(i2csocket,options.process,options.subprocess,options.odir,options.dut,options.device_type,options.directory_index, options.calib, options.LEDvolt, options.overvoltage, options.cfgF, suffix=options.suffix)
