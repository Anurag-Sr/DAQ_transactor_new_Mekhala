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

cm_dacb_vals = {0:45,4:33,8:20,12:12}

Sign_dac_default = 0

# pedestal scan
def pedestal_scan(i2csocket,daqsocket, clisocket, basedir,device_name,configFile,convgain):
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
    
    #for Dacb_val in Dacb_vals:
    nestedConf = nested_dict()
    for key in i2csocket.yamlConfig.keys():
        if key.find('roc_s')==0:
            nestedConf[key]['sc']['GlobalAnalog']['all']['Gain_conv']=convgain
            nestedConf[key]['sc']['cm']['all']['Dacb']=cm_dacb_vals[convgain]
            nestedConf[key]['sc']['calib']['all']['Dacb']=cm_dacb_vals[convgain]
            print("cm and calib set to",cm_dacb_vals[convgain],"for CGain",convgain)
                    
            Dacb_vals = [cm_dacb_vals[convgain]-10,cm_dacb_vals[convgain]]
            for i,Dacb_val in enumerate(Dacb_vals):
                nestedConf[key]['sc']['ch']['all']['Dacb']=Dacb_val
                i2csocket.configure(yamlNode=nestedConf.to_dict())
                util.acquire_scan(daq=daqsocket)
                chip_params = {'Dacb' : Dacb_val}
                util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,
                                  runid=i,testName=testName,keepRawData=0,
                                  chip_params=chip_params)
        
        
    clisocket.stop()
    mylittlenotifier.stop()
    
    dataPd = pd.DataFrame()
    
    for i,Dacb_val in enumerate(Dacb_vals):
        f = uproot.open(os.path.join(odir,"pedestal_scan%i.root"%i))
        dataPd[Dacb_val] = f['runsummary']['summary']['adc_mean'].array(library='np')
            
    with open(configFile) as f:
        cfg = yaml.safe_load(f)
        
    calib_i =0
    cm_i    =0
    chan_i  =0 
    
    ped_needed = dataPd[cm_dacb_vals[convgain]]
    print(ped_needed[ped_needed.index >= np.min(cm_ch)])
    ped_needed = ped_needed[ped_needed.index >= np.min(cm_ch)].mean()
    print("ped_needed:",ped_needed)
     
    cfg["roc_s0"]['sc']['GlobalAnalog']['all']['Gain_conv']=convgain
    for chan in range(0,len(dataPd)):  
        y = np.array(dataPd.loc[chan])
        grad  = (y[1]-y[0])/(Dacb_vals[1]-Dacb_vals[0])
        offset = y[0] - Dacb_vals[0]*grad
        if grad == 0:         
            dacb_val_signed = 63
            print("gradient was zero")
        else: 
            dacb_val = int((ped_needed-offset)/grad)
            if dacb_val >63:
                print("signdac=1")
                Sign_dac = 1
                dacb_val_signed = 2*63 - dacb_val
            else:
                dacb_val_signed = dacb_val
                Sign_dac = 0
        
        if chan in calib_ch:
            cfg["roc_s0"]["sc"]["calib"][calib_i]['Dacb']= cm_dacb_vals[convgain]
            print("calib_i",calib_i)
            grad = 0
            calib_i += 1
        elif chan in cm_ch:
            cfg["roc_s0"]["sc"]["cm"][cm_i]['Dacb']= cm_dacb_vals[convgain]
            print("cm_i",cm_i)
            grad = 0
            cm_i += 1
        else:
            cfg["roc_s0"]["sc"]["ch"][chan_i]["Dacb"] = dacb_val_signed
            print("chan_i",chan_i)
            chan_i += 1
            
        if grad != 0:
            print(grad,offset)
            print(dacb_val_signed)
            print(grad*dacb_val+offset)
        else :
            print(Sign_dac_default,cm_dacb_vals[convgain])
        
    configFile0 = configFile[:configFile.find("0_default")]
    with open(configFile0+str(convgain)+".yaml", "w") as o:
        yaml.dump(cfg, o)
    print("Saved new config file as:"+configFile0+str(convgain)+".yaml")        

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
    for convgain in [0,4,8,12]:
        pedestal_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.configFile,convgain)
    
