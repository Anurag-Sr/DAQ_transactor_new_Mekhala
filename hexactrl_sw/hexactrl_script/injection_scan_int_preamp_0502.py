import zmq, datetime,  os, subprocess, sys, yaml, glob
from time import sleep

import pandas
from level0.analyzer import *
import myinotifier,util
import analysis.level0.injection_scan_analysis as analyzer
import zmq_controler as zmqctrl
import miscellaneous_functions as misc_func
from nested_dict import nested_dict

def scan(i2csocket, daqsocket, injectedChannels, calib_dac_vals, gain, odir,phase,keepRawData=0):
    testName = 'injection_scan'

    index=0
    myphase = phase
    i2csocket.phase_set(myphase)
    ### added from Mathias
    nestedConf = nested_dict()
    #chronological order changed a little bit, did not want to add yet another function for this
    [nestedConf[key]['sc']['ch']['all'].update({'LowRange':0}) for key in i2csocket.yamlConfig.keys() if key.find('roc_s')==0 ]   # Reset injection first. 
    [nestedConf[key]['sc']['ch']['all'].update({'HighRange':0}) for key in i2csocket.yamlConfig.keys() if key.find('roc_s')==0 ]   # Reset injection first. 

    #Setting the preamp and conveyor calib both to 0 here because both have not been set here, might get rid of this function call completely at a later stage
    #Here even in the low range and high range settings (according to the values) they have just assumed that the gain would be 1, setting ranges for other gain values according to binary encoding
    i2csocket.configure_injection(trim_val = 0, process = 'int', calib_preamp = 0, calib_conv = 0, gain=gain,injectedChannels=injectedChannels, IntCtest = 1, choice_cinj = 1, cmd_120p = 0, L_g2 = 1, H_g2 = 1, L_g1 = 0, H_g1 = 1, L_g0 = 1, H_g0 = 0)    
    '''
    for key in i2csocket.yamlConfig.keys():
        print("Marke 1")
        if key.find('roc_s')==0:
            print("Marke2")
            nestedConf[key]['sc']['ReferenceVoltage']['all']['IntCtest'] = 1  # "0": injection into conveyor, "1": preamp injection
            print("Marke 3")
            nestedConf[key]['sc']['ReferenceVoltage']['all']['choice_cinj'] = 1   # "1": inject to preamp input, "0": inject to conveyor input
            nestedConf[key]['sc']['ReferenceVoltage']['all']['cmd_120p'] = 0 # cmd_120p=0: Cinj=3pF, cmd_120p=1: Cinj=120pF. Only Conveyor!!
            #nestedConf[key]['sc']['Top']['all']['phase_ck']=myphase
            #print(" Phase set: ", myphase)

            for inj_chs in injectedChannels:
                   print(" Gain=1, Channel: ", inj_chs)
                   [nestedConf[key]['sc']['ch'][inj_chs].update({'LowRange':0}) for key in i2csocket.yamlConfig.keys() if key.find('roc_s')==0 ] 
                   [nestedConf[key]['sc']['ch'][inj_chs].update({'HighRange':1}) for key in i2csocket.yamlConfig.keys() if key.find('roc_s')==0 ] 
    i2csocket.configure(yamlNode=nestedConf.to_dict())
    '''
    ### end added part
    
        
    for calibDAC_val in calib_dac_vals:
        print ("Pulse height for this run number", index, calibDAC_val)
        #True to the definition of sipm_configure_injection, the calib_conv will be set to the desired calib (pulse height) value here, but the other (IntCtest etc) options are also not consistent with the preamp stage, but with the conveyor stage
        #i2csocket.configure_injection(trim_val = 0, process = 'int', calib_preamp = 0, calib_conv = calibDAC_val, gain=gain,injectedChannels=injectedChannels, IntCtest = 1, choice_cinj = 1, cmd_120p = 0, L_g2 = 1, H_g2 = 1, L_g1 = 0, H_g1 = 1, L_g0 = 1, H_g0 = 0)    
        i2csocket.configure_injection(trim_val = 0, process = 'int', calib_preamp = calibDAC_val, calib_conv = 0, gain=gain,injectedChannels=injectedChannels, IntCtest = 1, choice_cinj = 1, cmd_120p = 0, L_g2 = 1, H_g2 = 1, L_g1 = 0, H_g1 = 1, L_g0 = 1, H_g0 = 0)    
        
        #i2csocket.sipm_configure_injection(injectedChannels, activate=1, gain=gain, calib_dac=calibDAC_val)
        # i2csocket.sipm_configure_injection(injectedChannels, activate=1, gain=gain, calib_dac=0)
        
        # nestedConf[key]['sc']['ReferenceVoltage']['all']['Calib_2V5'] = calibDAC_val
        # i2csocket.configure(yamlNode=nestedConf.to_dict())
        
        # i2csocket.configure_injection(injectedChannels, activate=1, gain=gain, calib_dac=calibDAC_val)
        util.acquire_scan(daq=daqsocket)
        # chip_params = { 'Inj_gain':gain, 'Calib_dac':calibDAC_val }
        #chip_params = { 'gain':gain, 'Calib':calibDAC_val, 'injectedChannels':injectedChannels[0] } #Why only the first one??
        chip_params = { 'gain':gain, 'Calib':calibDAC_val, 'injectedChannels':injectedChannels }
        util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,
                          runid=index,testName=testName,keepRawData=keepRawData,
                          chip_params=chip_params)
        index+=1
    return

def sipm_injection_scan(i2csocket,daqsocket,clisocket,basedir,device_name,device_type, injectionConfig,scurve_scan,suffix='', active_menu = 'calibAndL1AplusTPG',keepRawData=1,analysis=1):
    testName='PreampInjection_scan'
    if scurve_scan == 0: #No scurve scans over trim toa, just normal injection scans over chosen channels
        odir = misc_func.mkdir(os.path.realpath(basedir),device_type,testName = testName,suffix=suffix)    
    elif scurve_scan == 1:
        odir = misc_func.mkdir(os.path.realpath(basedir),testName = testName,suffix=suffix)
     # do not run the inotifier if the unpacker is not yet ready to read vectors inside metaData yaml file using key "chip_params"
    mylittlenotifier = myinotifier.mylittleInotifier(odir=odir)
    
    calibreq            = 0x10
    calibreqC            = 0x200 #What is this and why is it not used anywhere else?
    BXoffset			= injectionConfig['BXoffset']
    injectedChannels	= injectionConfig['injectedChannels']
    
    calib_dac 			= injectionConfig['calib']
    gain 				= injectionConfig['gain'] # 0 for low range ; 1 for high range
    phase               = injectionConfig['phase']
    clisocket.yamlConfig['client']['outputDirectory'] = odir
    clisocket.yamlConfig['client']['run_type'] = "injection_scan"
    clisocket.configure()
    
    #daqsocket.daq_sampling_scan_settings(active_menu = 'calibAndL1A', num_events = 500, calibType = 'CALPULINT', lengthCalib = 1, lengthL1A = 1, bxCalib = calibreq, bxL1A = calibreq+BXoffset, prescale = 0, repeatOffset = 0)
    '''
    # original setup without trigger data
    
    daqsocket.yamlConfig['daq']['active_menu']='calibAndL1A'
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['calibType']="CALPULINT"  
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['NEvents']=500
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxCalib']=calibreq
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxL1A']=calibreq+BXoffset
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthCalib']=1
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthL1A']=1 #1
    daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['prescale']=0
    #Just for external injeciton (to enable the SiPM calib signal):
    #daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['calibType']='CALPULEXT'
    daqsocket.configure()
    
    '''
    daqsocket.daq_sampling_scan_settings(active_menu = active_menu, num_events = 500, calibType = 'CALPULINT', lengthCalib = 1, lengthL1A = 1, bxCalib = calibreq, bxL1A = calibreq+BXoffset, prescale = 0, repeatOffset = 0)
    if active_menu == 'calibAndL1AplusTPG': #Extra setting that may not be present in calibAndL1A
        daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['trg_fifo_latency']=3 # set to 1 or 2
    
    '''
    daqsocket.yamlConfig['daq']['active_menu']='calibAndL1AplusTPG'
    daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['calibType']="CALPULINT"  
    daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['NEvents']=500
    daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['bxCalib']=calibreq
    daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['bxL1A']=calibreq+BXoffset
    daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['trg_fifo_latency']=3 # set to 1 or 2
    daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['lengthCalib']=1
    daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['lengthL1A']=1
    daqsocket.yamlConfig['daq']['menus']['calibAndL1AplusTPG']['prescale']=0
    '''
    daqsocket.configure()
    
    util.saveFullConfig(odir=odir,i2c=i2csocket,daq=daqsocket,cli=clisocket,filename = 'initial_full_config.yaml')
    
    clisocket.start()
    mylittlenotifier.start()
    scan(i2csocket=i2csocket, daqsocket=daqsocket, injectedChannels=injectedChannels, calib_dac_vals=calib_dac, gain=gain, odir=odir,phase=phase,keepRawData=keepRawData)
    mylittlenotifier.stop()
    clisocket.stop()
    
    # return to no injection setting
    i2csocket.configure_injection(trim_val = 0, process = 'int', calib_preamp = 0, calib_conv = 0, gain=gain,injectedChannels=injectedChannels, IntCtest = 0, choice_cinj = 0, cmd_120p = 0, L_g2 = 0, H_g2 = 0, L_g1 = 0, H_g1 = 0, L_g0 = 0, H_g0 = 0)
    #i2csocket.sipm_configure_injection(injectedChannels, activate=0, gain=0, calib_dac=0) #maybe we should go back to phase 0
    
    if analysis == 1:
        scan_analyzer = analyzer.injection_scan_analyzer(odir=odir)
        files = glob.glob(odir+"/*.root")
        for f in files:
            scan_analyzer.add(f)
            # r_summary = reader(f)
            # r_raw = rawroot_reader(f)
            # r_raw.df['Calib_dac'] = r_summary.df.Calib_dac.unique()[0]
            # scan_analyzer.dataFrames.append(r_raw.df)
        scan_analyzer.mergeData()
        scan_analyzer.makePlots()

        ''' 
        max_dict = scan_analyzer.determineAdcRange(injectedChannels)
        print("max_dict ", max_dict)
        max_calib = min(max_dict.values())
        print("max_calib ", max_calib)
        '''
        
    # return odir, max_dict
    return odir


if __name__ == "__main__":
    parser = misc_func.options_run()#This will be constant for every test irrespective of the type of test
    
    (options, args) = parser.parse_args()
    print(options)
    (daqsocket,clisocket,i2csocket) = zmqctrl.pre_init(options)
             
    injectionConfig = {
        #'BXoffset' : 21,   # was 22
        'BXoffset' : 22,   # was 22, this is for BX 22 because of the sculpting of the pulse shape due to change in number of injection channels per half
        'gain' : 1,
        'phase' : 2,
        # 'calib' : [-1]+[i for i in range(0,4000,100)],
        # 'calib' : [i for i in range(0,400,2)],
        'calib' : [i for i in range(0,2000,25)],
        #'calib' : [i for i in range(0,4000,50)], #Observed some weird saturation for 5 injected channels, that is why the range was extended
        
        #'injectedChannels' : [6, 10, 45, 52]  # TRIG1
        'injectedChannels' : [2, 4, 6, 8, 10, 45, 52, 48, 53, 63]  # TRIG1
        #'injectedChannels' : [6, 10, 45, 52, 48, 53, 63]  # TRIG1
        # 'injectedChannels' : [15, 48]  # TRIG2
        # 'injectedChannels' : [23, 58]  # TRIG3
        # 'injectedChannels' : [32, 67]  # TRIG4
    }
    sipm_injection_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.device_type,injectionConfig,scurve_scan = 0,suffix=options.suffix,keepRawData=0,analysis=1)
