import zmq, datetime,  os, subprocess, sys, yaml, glob
from time import sleep
from nested_dict import nested_dict

import pandas
from level0.analyzer import *
import myinotifier,util
import analysis.level0.sampling_scan_analysis as analyzer
import zmq_controler as zmqctrl
# from Tektronix_AFG3102_ExtTrig import *

def scan(i2csocket, daqsocket, startBX, stopBX, stepBX, startPhase, stopPhase, stepPhase, injectedChannels, odir, extInj=None):
    testName='sampling_scan'

    index=0
    for BX in range(startBX, stopBX, stepBX):
        # if extInj == None:
        daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxL1A']=BX
        print(yaml.dump(daqsocket.yamlConfig['daq']['menus']) )
        #daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['bxL1A']=BX
        daqsocket.configure()
        # daqsocket.l1a_generator_settings(name='B',enable=1,BX=BX,length=1,flavor='L1A',prescale=0,followMode='A')
        # else:
        #     daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxL1A']=BX
        #     daqsocket.configure()

        for phase in range(startPhase,stopPhase+1,stepPhase):
            nestedConf = nested_dict()
            for key in i2csocket.yamlConfig.keys():
                if key.find('roc_s')==0:
                    nestedConf[key]['sc']['Top']['all']['phase_ck']=phase
            i2csocket.configure(yamlNode=nestedConf.to_dict())
            i2csocket.resettdc()	# Reset MasterTDCs

            util.acquire_scan(daq=daqsocket)
            if extInj == None:
                chip_params = { 'BX' : BX-startBX, 'Phase' : phase, 'injectedChannel':injectedChannels[0] }
            else:
                chip_params = { 'BX' : BX-startBX, 'Phase' : phase, 'extInj' : extInj, 'injectedChannel':injectedChannels[0] }
                
            util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,
                              runid=index,testName=testName,keepRawData=1,
                              chip_params=chip_params)
            index=index+1
    return

def scan_BX(i2csocket, daqsocket, startBX, stopBX, stepBX, startPhase, stopPhase, stepPhase, injectedChannels, odir, calib_2V5, gain, gainconv, extInj=None):
    testName='sampling_scan'
    length = stopBX - startBX
    index=0

    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxL1A']=startBX
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthL1A']=length
    #daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['bxL1A']=startBX
    #daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['lengthL1A']=length
    daqsocket.configure()

    for phase in range(startPhase,stopPhase+1,stepPhase):
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys():
            if key.find('roc_s')==0:
                nestedConf[key]['sc']['Top']['all']['phase_ck']=phase
        i2csocket.update_yamlConfig(yamlNode=nestedConf.to_dict())
        i2csocket.configure(yamlNode=nestedConf.to_dict())
        i2csocket.resettdc()	# Reset MasterTDCs

        util.acquire_scan(daq=daqsocket)
        if extInj == None:
            chip_params = { 'BX' : startBX, 'Phase' : phase, 'Calib_dac_2V5' : calib_2V5, 'gain' : gain, 'Gain_conv' : gainconv, 'injectedChannel' : injectedChannels[0] }
        else:
            chip_params = { 'BX' : startBX, 'Phase' : phase, 'extInj' : extInj, 'gain' : gain, 'Gain_conv' : gainconv, 'injectedChannel' : injectedChannels[0] }

        util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,
                          runid=index,testName=testName,keepRawData=1,
                          chip_params=chip_params)
        index=index+1
    return

def sipm_sampling_scan(i2csocket,daqsocket, clisocket, basedir,device_name, injectionConfig,suffix,extInj=0):
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
    odir = "%s/%s/sampling_scan/run_%s/"%( os.path.realpath(basedir), device_name, timestamp ) # a complete path is needed
    os.makedirs(odir)
    print(odir)
    mylittlenotifier = myinotifier.mylittleInotifier(odir=odir)

    startPhase=0
    stopPhase=14 #15
    stepPhase=1

    clisocket.yamlConfig['client']['outputDirectory'] = odir
    clisocket.yamlConfig['client']['run_type'] = "sampling_scan"
    clisocket.configure()
    
    # calibreq = 0x10
    if extInj == 0:
        calibreq = 0x10
        bxoffset = 22 #21
        window_offset = 0
    elif extInj ==1:
        calibreq = 0x10
        bxoffset = 31 #24 Laser, 31 extInj
        window_offset = 0
    startBX=calibreq+bxoffset - 1 # -1
    stopBX=calibreq+bxoffset + 6 + window_offset # 6, 20
    stepBX=1
    daqsocket.yamlConfig['daq']['active_menu']='calibAndL1A'
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['NEvents']=1000
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxCalib']=calibreq
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxL1A']=calibreq+bxoffset #New
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthCalib']=1
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthL1A']=1
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['prescale']=0
    # daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['repeatOffset']=700 #New
    if extInj ==1:
        daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['calibType']='CALPULEXT'

    gain = injectionConfig['gain'] # 0 for low range ; 1 for high range
    if extInj ==0:
        calib = injectionConfig['calib'] # 
        print("calib = %i" %injectionConfig['calib'])
    elif extInj ==1:
        ### Voltage generator:
        # calib = injectionConfig['volt_amp'] # 
        # print("calib = %i" %injectionConfig['volt_amp'])
        # volt_amp = calib
        volt_amp = injectionConfig['volt_amp'] #volt_amp in mV
        volt_amp_stop = injectionConfig['volt_amp_stop'] #voltage maximum of tektronix is 10V
        print("volt_amp = %imV, volt_amp_stop = %imV" %(injectionConfig['volt_amp'],injectionConfig['volt_amp_stop']))
    injectedChannels=injectionConfig['injectedChannels']
    print("gain = %i" %injectionConfig['gain'])

    if 'gainconv' in injectionConfig:
        print("gainconv = %i" %injectionConfig['gainconv'])    
        gainconv = injectionConfig['gainconv']  
    else:
        gainconv = None

    util.saveFullConfig(odir=odir,i2c=i2csocket,daq=daqsocket,cli=clisocket)

    if extInj == 0:
        i2csocket.sipm_configure_injection(injectedChannels, activate=1, gain=gain, phase=0, calib=calib)
        # i2csocket.configure_injection(injectedChannels, activate=1, gain=gain, phase=0, calib_dac=calib)
    elif extInj ==1:
        i2csocket.sipm_configure_injection(injectedChannels, activate=0, gain=0, phase=0, calib=0)
        # print("Configure Tektronix Amplitude to:", volt_amp/1000)
        # read_tek("Send_" + str(volt_amp/1000), volt_amp/1000, volt_amp_stop/1000)

    clisocket.start()
    mylittlenotifier.start()
    if extInj == 0:
        scan(i2csocket=i2csocket, daqsocket=daqsocket, 
            startBX=startBX, stopBX=stopBX, stepBX=stepBX, 
            startPhase=startPhase, stopPhase=stopPhase, stepPhase=stepPhase, 
            injectedChannels=injectedChannels, odir=odir, gainconv=gainconv, calib_val=calib, gain=gain)
        # scan_BX(i2csocket=i2csocket, daqsocket=daqsocket, 
        #     startBX=startBX, stopBX=stopBX, stepBX=stepBX, 
        #     startPhase=startPhase, stopPhase=stopPhase, stepPhase=stepPhase, 
        #     injectedChannels=injectedChannels, odir=odir, calib_2V5=calib, gain=gain, gainconv=gainconv, calibrationConfig=calibrationConfig)
    elif extInj == 1:
        scan(i2csocket=i2csocket, daqsocket=daqsocket, 
            startBX=startBX, stopBX=stopBX, stepBX=stepBX, 
            startPhase=startPhase, stopPhase=stopPhase, stepPhase=stepPhase, 
            injectedChannels=injectedChannels, odir=odir, extInj=volt_amp, gainconv=gainconv)
        # scan_BX(i2csocket=i2csocket, daqsocket=daqsocket, 
        #     startBX=startBX, stopBX=stopBX, stepBX=stepBX, 
        #     startPhase=startPhase, stopPhase=stopPhase, stepPhase=stepPhase, 
        #     injectedChannels=injectedChannels, odir=odir, calib_2V5=0, gain=gain, calibrationConfig=calibrationConfig, extInj=volt_amp)
    mylittlenotifier.stop()
    clisocket.stop()

    ###### ANALYSIS:
    scan_analyzer = analyzer.sampling_scan_analyzer(odir=odir)
    files = glob.glob(odir+"/"+clisocket.yamlConfig['client']['run_type']+"*.root")

    df_ = []
    for f in files:
        # df = uproot3.open(f)['unpacker_data']['hgcroc'].pandas.df()
        r_summary = reader(f)
        # df['Phase'] = r_summary.df.Phase.unique()[0]
        df_.append(r_summary.df)
    scan_analyzer.data = pandas.concat(df_)
    ###
    scan_analyzer.makePlots()
    # scan_analyzer.makePlots_plusStd(injectedChannels)
    try:
        # scan_analyzer.determine_bestPhase(injectedChannels)
        scan_analyzer.determine_bestPhase_simple(injectedChannels)
    except:
        pass

    # return to no injection setting
    i2csocket.sipm_configure_injection(injectedChannels,activate=0,calib=0,phase=None,gain=0) 

    try:
        with open(odir+'/best_phase.yaml') as fin:
            cfg = yaml.safe_load(fin)
            i2csocket.configure(yamlNode=cfg)
            i2csocket.update_yamlConfig(yamlNode=cfg)
    except:
        yaml_dict = {}
        yaml_dict['roc_s0'] = {
            'sc' : {
                'Top' : { 
                    'all': { #0
                        'phase_ck': 'Error'
                        }
                    }
                }
            }
        with open(odir+'/best_phase_error.yaml','w') as fout:
            yaml.dump(yaml_dict,fout)
        pass

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

    parser.add_option("-e", "--extInj",
                      action="store", dest="extInj",default=0, type=int,
                      help="0 = Internal Injection; 1 = External Injection")
    
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
    i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort,options.configFile)
    
    if options.initialize==True:
        i2csocket.initialize()
        daqsocket.initialize()
        clisocket.yamlConfig['client']['serverIP'] = daqsocket.ip
        clisocket.initialize()
    else:
        i2csocket.configure()

    if options.extInj == 0:
        injectionConfig = {
            'gain' : 0,
            'calib' : 1000,
            'injectedChannels' : [11,11+36]
        }
    elif options.extInj == 1:
        injectionConfig = {
            'gain' : 0,
            'volt_amp' : 500, #mV
            'volt_amp_stop' : 5000, #mV
            'injectedChannels' : [11,11+36]
        }
    sipm_sampling_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,injectionConfig,suffix=options.suffix,extInj=options.extInj)

