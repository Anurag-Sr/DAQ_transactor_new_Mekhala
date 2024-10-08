import zmq, datetime,  os, subprocess, sys, yaml, glob
from time import sleep

import myinotifier,util
import analysis.level0.pedestal_scan_analysis as analyzer
import zmq_controler as zmqctrl
from nested_dict import nested_dict

import uproot
import pandas as pd
import numpy as np

calib_ch = [72,73]
cm_ch    = [74,75,76,77]

DACb = 63

# pedestal scan
def scan_pedDAC(i2csocket, daqsocket, start, stop, step, odir):
    testName='pedestal_scan'
    
    index=0
    for ref_val in range(start,stop,step):
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys():
            if key.find('roc_s')==0:
                nestedConf[key]['sc']['ch']['all']['trim_inv']=ref_val
                nestedConf[key]['sc']['cm']['all']['trim_inv']=ref_val
                nestedConf[key]['sc']['calib']['all']['trim_inv']=ref_val
        i2csocket.configure(yamlNode=nestedConf.to_dict())
        util.acquire_scan(daq=daqsocket)
        chip_params = {'trim_inv' : ref_val }
        util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,
                          runid=index,testName=testName,keepRawData=0,
                          chip_params=chip_params)
        index=index+1
    return

def pedestal_scan(i2csocket,daqsocket, clisocket, basedir,device_name,configFile):
    if type(i2csocket) != zmqctrl.i2cController:
	    print( "ERROR in pedestal_run : i2csocket should be of type %s instead of %s"%(zmqctrl.i2cController,type(i2csocket)) )
	    sleep(1)
	    return

    if type(daqsocket) != zmqctrl.daqController:
	    print( "ERROR in pedestal_run : daqsocket should be of type %s instead of %s"%(zmqctrl.daqController,type(daqsocket)) )
	    sleep(1)
	    return

    if type(clisocket) != zmqctrl.daqController:
	    print( "ERROR in pedestal_run : clisocket should be of type %s instead of %s"%(zmqctrl.daqController,type(clisocket)) )
	    sleep(1)
	    return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    odir = "%s/%s/pedestal_scan/run_%s/"%( os.path.realpath(basedir), device_name, timestamp ) # a comlete path is needed
    os.makedirs(odir)
    
    mylittlenotifier = myinotifier.mylittleInotifier(odir=odir)
    mylittlenotifier.start()

    start_val=0
    stop_val=32
    step_val=1

    clisocket.yamlConfig['global']['outputDirectory'] = odir
    clisocket.yamlConfig['global']['run_type'] = "pedestal_scan"
    clisocket.yamlConfig['global']['serverIP'] = daqsocket.ip
    clisocket.configure()
    daqsocket.enable_fast_commands(random=1)
    daqsocket.l1a_settings(bx_spacing=45)
    daqsocket.yamlConfig['daq']['NEvents']='5000'
    daqsocket.configure()

    util.saveFullConfig(odir=odir,i2c=i2csocket,daq=daqsocket,cli=clisocket)
            
    clisocket.start()
    #scan_pedDAC(i2csocket, daqsocket, start_val, stop_val, step_val,odir)
    
    testName='pedestal_scan'
    
    
    index=0
    ref_vals = [0,8,16,24]
    for i,ref_val in enumerate(ref_vals):
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys():
            if key.find('roc_s')==0:
                nestedConf[key]['sc']['ch']['all']['trim_inv']=ref_val
                nestedConf[key]['sc']['cm']['all']['trim_inv']=ref_val
                nestedConf[key]['sc']['calib']['all']['trim_inv']=ref_val
                
                nestedConf[key]['sc']['ch']['all']['Dacb']=DACb
                nestedConf[key]['sc']['cm']['all']['Dacb']=DACb
                nestedConf[key]['sc']['calib']['all']['Dacb']=DACb
                
        i2csocket.configure(yamlNode=nestedConf.to_dict())
        util.acquire_scan(daq=daqsocket)
        chip_params = {'trim_inv' : ref_val ,'Dacb':DACb}
        util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,
                          runid=i,testName=testName,keepRawData=0,
                          chip_params=chip_params)
        
        
    clisocket.stop()
    mylittlenotifier.stop()
    
    dataPd = pd.DataFrame()
    for i,ref_val in enumerate(ref_vals):
        f = uproot.open(os.path.join(odir,"pedestal_scan%i.root"%i))
        dataPd[ref_val] = f['runsummary']['summary']['adc_mean'].array(library='np')
        #dataPd[ref_val] = f['runsummary']['summary'].arrays(['adc_mean','channeltype'],library='np')
    
    with open(configFile) as f:
        cfg = yaml.safe_load(f)
        
    ped_chan = []
    calib_i =0
    cm_i    =0
    chan_i  =0 
    
    ped_needed = dataPd[0].max()
    print("ped_needed:",ped_needed,"channel:",dataPd[0].argmax())
    for chan in range(0,len(dataPd)):  
        y = np.array(dataPd.loc[chan])
        grad  = (y[3]-y[1])/(ref_vals[3]-ref_vals[1])
        offset = y[3] - ref_vals[3]*grad
        '''
        A = int((ped_needed-offset)/grad)
        
        ped_chan.append(int((ped_needed-offset)/grad))
        y = np.array(dataPd.loc[chan])
        grad  = (y[1]-y[0])/(ref_vals[1]-ref_vals[0])
        offset = y[1] - ref_vals[1]*grad
        B = int((ped_needed-offset)/grad)
        
        y = np.array(dataPd.loc[chan])
        grad  = (y[2]-y[1])/(ref_vals[2]-ref_vals[1])
        offset = y[2] - ref_vals[2]*grad
        C = int((ped_needed-offset)/grad)
        print(A,B,C)        
        '''
        
        if chan in calib_ch:
            cfg["roc_s0"]["sc"]["calib"][calib_i]["trim_inv"] = int((ped_needed-offset)/grad)
            cfg["roc_s0"]["sc"]["calib"][calib_i]['Dacb']=DACb
            print("calib_i",calib_i)
            calib_i += 1
            
        elif chan in cm_ch:
            cfg["roc_s0"]["sc"]["cm"][cm_i]["trim_inv"] = int((ped_needed-offset)/grad)
            cfg["roc_s0"]["sc"]["cm"][cm_i]['Dacb']=DACb
            print("cm_i",cm_i)
            cm_i += 1
        else:
            cfg["roc_s0"]["sc"]["ch"][chan_i]["trim_inv"] = int((ped_needed-offset)/grad)
            cfg["roc_s0"]["sc"]["ch"][chan_i]['Dacb']=DACb
            print("chan_i",chan_i)
            chan_i += 1
            
        print(int((ped_needed-offset)/grad))
        print(grad*int((ped_needed-offset)/grad)+offset)
        
    configFile0 = configFile[:configFile.find(".yaml")]
    with open(configFile0+"_triminv.yaml", "w") as o:
        yaml.dump(cfg, o)
    print("Saved new config file as:"+configFile0+"_triminv.yaml")        
    '''
    configFile4 = configFile[:configFile.find("4.yaml")]
    cfg["roc_s0"]["sc"]["GlobalAnalog"]["all"]["Gain_conv"] = 4
    with open(configFile4+"4_new.yaml", "w") as o:
        yaml.dump(cfg, o)
    '''
    return odir
    
    


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    
    parser.add_option("-d", "--dut", dest="dut",
                      help="device under test")
    
    parser.add_option("-i", "--hexaIP",
                      action="store", dest="hexaIP",
                      help="IP address of the zynq on the hexactrl board")
    
    parser.add_option("-f", "--configFile",default="./configs/init.yaml",
                      action="store", dest="configFile",
                      help="initial configuration yaml file")
    
    parser.add_option("-o", "--odir",
                      action="store", dest="odir",default='./data',
                      help="output base directory")
    
    parser.add_option("--daqPort",
                      action="store", dest="daqPort",default='6000',
                      help="port of the zynq waiting for daq config and commands (configure/start/stop/is_done)")
    
    parser.add_option("--i2cPort",
                      action="store", dest="i2cPort",default='5555',
                      help="port of the zynq waiting for I2C config and commands (initialize/configure/read_pwr,read/measadc)")
    
    parser.add_option("--pullerPort",
                      action="store", dest="pullerPort",default='6001',
                      help="port of the client PC (loccalhost for the moment) waiting for daq config and commands (configure/start/stop)")
    
    
    (options, args) = parser.parse_args()
    print(options)
    
    daqsocket = zmqctrl.daqController(options.hexaIP,options.daqPort,options.configFile)
    clisocket = zmqctrl.daqController("localhost",options.pullerPort,options.configFile)
    i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort,options.configFile)
    
    i2csocket.configure()
    pedestal_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.configFile)
    
