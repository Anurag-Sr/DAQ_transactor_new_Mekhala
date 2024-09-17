import datetime,  os, subprocess, sys, yaml, glob
from time import sleep

import uproot
import pandas as pd
import numpy as np

calib_ch = [72,73]
cm_ch    = [74,75,76,77]

DACb = 63

def configGenerator(odir,configFile):
    """
    This generator generates the three config files needed for DNL correction via 
    pedestal adjustment
    """
    
    with open(configFile) as f:
        cfg = yaml.safe_load(f)
    
    if not os.path.exists(odir): os.makedirs(odir)
    
    for triminv in [0,1,2]:
        for chan in range(np.min(calib_ch)):
            if triminv>0:
                cfg["roc_s0"]["sc"]["ch"][chan]["trim_inv"] = cfg["roc_s0"]["sc"]["ch"][chan]["trim_inv"]+1
            
        configFile0 = configFile.split("/")[-1]
        configFile0 = configFile0[:configFile0.find(".yaml")]
        with open(odir+"/"+configFile0+"_triminv"+str(triminv)+".yaml", "w") as o:
            yaml.dump(cfg, o)
        print("Saved new config file as:"+odir+"/"+configFile0+"_triminv"+str(triminv)+".yaml")  
    return odir
    
if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    
    parser.add_option("-f", "--configFile",default="./configs/init.yaml",
                      action="store", dest="configFile",
                      help="initial configuration yaml file")
    
    parser.add_option("-o", "--odir",
                      action="store", dest="odir",default='./configs/',
                      help="output base directory")
    
    
    (options, args) = parser.parse_args()
    print(options)
    
    configGenerator(options.odir,options.configFile)
    
