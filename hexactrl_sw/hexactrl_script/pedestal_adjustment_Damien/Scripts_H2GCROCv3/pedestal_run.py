import zmq, datetime,  os, subprocess, sys, yaml, glob

import myinotifier,util
import analysis.level0.pedestal_run_analysis as analyzer
import zmq_controler as zmqctrl
from nested_dict import nested_dict 

def pedestal_run(i2csocket,daqsocket, clisocket, basedir,device_name,suffix="",maindir=None):
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
    if suffix:
        timestamp = timestamp + "_" + suffix
    if maindir == None:
        maindir = "pedestal_run"
    testName = "pedestal_run"
    odir = "%s/%s/%s/run_%s/"%( os.path.realpath(basedir), device_name, maindir, timestamp )
    os.makedirs(odir)
    
    mylittlenotifier = myinotifier.mylittleInotifier(odir=odir)
    mylittlenotifier.start()
    
    clisocket.yamlConfig['client']['outputDirectory'] = odir
    clisocket.yamlConfig['client']['run_type'] = testName
    clisocket.configure()
    daqsocket.yamlConfig['daq']['active_menu']='randomL1A'
    daqsocket.yamlConfig['daq']['menus']['randomL1A']['NEvents']=10000
    daqsocket.yamlConfig['daq']['menus']['randomL1A']['log2_rand_bx_period']=0
    daqsocket.yamlConfig['daq']['menus']['randomL1A']['bx_min']=45
    # daqsocket.yamlConfig['daq']['active_menu']='randomL1AplusTPG'
    # daqsocket.yamlConfig['daq']['menus']['randomL1AplusTPG']['NEvents']=10000
    # daqsocket.yamlConfig['daq']['menus']['randomL1AplusTPG']['log2_rand_bx_period']=0
    # daqsocket.yamlConfig['daq']['menus']['randomL1AplusTPG']['bx_min']=45
    # daqsocket.yamlConfig['daq']['menus']['randomL1AplusTPG']['trg_fifo_latency']=5
    daqsocket.configure()
    	
    '''
    nestedConf = nested_dict()
    for key in i2csocket.yamlConfig.keys():
        if key.find('roc_s')==0:
            nestedConf[key]['sc']['ch'][0]['sel_trig_toa']=0
            nestedConf[key]['sc']['ch'][0+36]['sel_trig_toa']=0
    i2csocket.update_yamlConfig(yamlNode=nestedConf.to_dict())
    i2csocket.configure()
    '''
    util.saveFullConfig(odir=odir,i2c=i2csocket,daq=daqsocket,cli=clisocket)
    util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,runid=0,testName=testName,keepRawData=1,chip_params={})

    util.acquire(daq=daqsocket, client=clisocket)
    mylittlenotifier.stop()

    try:
        ped_analyzer = analyzer.pedestal_run_analyzer(odir=odir)
        files = glob.glob(odir+"/*.root")
    	
        for f in files:
    	    ped_analyzer.add(f)
    
        ped_analyzer.mergeData()
        ped_analyzer.makePlots()
        ped_analyzer.findPedMean()
        ped_analyzer.addSummary()
        ped_analyzer.writeSummary()
    except:
        with open(odir+"crash_report.log","w") as fout:
            fout.write("analysis went wrong and crash\n")

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
    
    parser.add_option("-s", "--suffix",
                      action="store", dest="suffix",default='',
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
    
    parser.add_option("-I", "--initialize",default=False,
                      action="store_true", dest="initialize",
                      help="set to re-initialize the ROCs and daq-server instead of only configuring")

    (options, args) = parser.parse_args()
    print(options)
    if not options.hexaIP:
        options.hexaIP = '129.104.89.111'
    print(options.hexaIP)
    
    daqsocket = zmqctrl.daqController(options.hexaIP,options.daqPort,options.configFile)
    clisocket = zmqctrl.daqController("localhost",options.pullerPort,options.configFile)
    clisocket.yamlConfig['client']['serverIP'] = options.hexaIP
    i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort,options.configFile)

    if options.initialize==True:
        i2csocket.initialize()
        daqsocket.initialize()
        clisocket.yamlConfig['client']['serverIP'] = daqsocket.ip
        clisocket.initialize()
    else:
        i2csocket.configure()
    pedestal_run(i2csocket,daqsocket,clisocket,options.odir,options.dut,suffix=options.suffix)
