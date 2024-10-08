import zmq, datetime,  os, subprocess, sys, yaml, glob
from time import sleep

import myinotifier,util
import analysis.level0.vrefnoinv_scan_analysis as analyzer
import zmq_controler as zmqctrl
from nested_dict import nested_dict

# noinv_vref scan
def scan(i2csocket, daqsocket, start, stop, step, odir):
    testName='vrefnoinv_scan'
    
    index=0
    for vref_val in range(start,stop,step):
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys():
            if key.find('roc_s')==0:
                nestedConf[key]['sc']['ReferenceVoltage'][0]['Noinv_vref']=vref_val
                nestedConf[key]['sc']['ReferenceVoltage'][1]['Noinv_vref']=vref_val
        i2csocket.configure(yamlNode=nestedConf.to_dict())
        util.acquire_scan(daq=daqsocket)
        chip_params = {'Noinv_vref' : vref_val }
        util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,
                          runid=index,testName=testName,keepRawData=0,
                          chip_params=chip_params)
        index=index+1
    return

def vrefnoinv_scan(i2csocket,daqsocket, clisocket, basedir,device_name,configFile):
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
    odir = "%s/%s/vrefnoinv_scan/run_%s/"%( os.path.realpath(basedir), device_name, timestamp ) # a comlete path is needed
    os.makedirs(odir)
    
    mylittlenotifier = myinotifier.mylittleInotifier(odir=odir)
    mylittlenotifier.start()
    
    start_val=0
    stop_val=350
    step_val=10
	
    clisocket.yamlConfig['global']['outputDirectory'] = odir
    clisocket.yamlConfig['global']['run_type'] = "vrefnoinv_scan"
    clisocket.yamlConfig['global']['serverIP'] = daqsocket.ip
    clisocket.configure()
    daqsocket.enable_fast_commands(random=1)
    daqsocket.l1a_settings(bx_spacing=45)
    daqsocket.yamlConfig['daq']['NEvents']='500'
    daqsocket.configure()
       
    util.saveFullConfig(odir=odir,i2c=i2csocket,daq=daqsocket,cli=clisocket)

    clisocket.start()
    scan(i2csocket, daqsocket, start_val, stop_val, step_val,odir)
    clisocket.stop()
    mylittlenotifier.stop()
    
    vrefnoinv_analyzer = analyzer.vrefnoinv_scan_analyzer(odir=odir)
    files = glob.glob(odir+"/*.root")
    
    for f in files:
	    vrefnoinv_analyzer.add(f)
    vrefnoinv_analyzer.mergeData()
    yaml_dict = vrefnoinv_analyzer.determine_bestVrefnoinv()
    vrefnoinv_analyzer.makePlots()
    
    with open(configFile) as f:
        cfg = yaml.safe_load(f)
        
    cfg["roc_s0"]["sc"]["ReferenceVoltage"][0]["Noinv_vref"] = yaml_dict["roc_s0"]["sc"]["ReferenceVoltage"][0]["Noinv_vref"]
    cfg["roc_s0"]["sc"]["ReferenceVoltage"][1]["Noinv_vref"] = yaml_dict["roc_s0"]["sc"]["ReferenceVoltage"][1]["Noinv_vref"]
        
    configFile0 = configFile[:configFile.find(".yaml")]
    with open(configFile0+"_Vrefnoinv.yaml", "w") as o:
        yaml.dump(cfg, o)
    print("Saved new config file as:"+configFile0+"_Vrefnoinv.yaml")  
    

    i2csocket.update_yamlConfig(fname=odir+'/vrefnoinv.yaml') #next step keeps the knowledge of what was changed
    i2csocket.configure(fname=odir+'/vrefnoinv.yaml')
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
    vrefnoinv_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.configFile)
