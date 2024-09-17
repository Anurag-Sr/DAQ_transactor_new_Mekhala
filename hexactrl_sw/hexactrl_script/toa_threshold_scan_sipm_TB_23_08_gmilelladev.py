import zmq, datetime,  os, subprocess, sys, yaml, glob
from time import sleep

from level0.analyzer import *
import myinotifier, util
import analysis.level0.toa_scan_analysis_TB_23_08_gmilelladev as analyzer
import zmq_controler as zmqctrl
from nested_dict import nested_dict
import numpy as np
import pandas
import sipm_injection_scan_conv_mat_TB_23_08 # Modified to the name you are using for the injection scan

def scan_toa_vref(i2csocket, daqsocket, startthr, stopthr, nstep, injectedChannels,odir,gain_tot=0,calib_dac_val=1800,keepRawData=0) :
    testName = 'toa_threshold_scan'
    index = 0
    for tot_vref_val in range(startthr, stopthr, nstep) :
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys() :
            if key.find('roc_s') == 0 :
                nestedConf[key]['sc']['ReferenceVoltage'][0]['Toa_vref'] = int(tot_vref_val)
                nestedConf[key]['sc']['ReferenceVoltage'][1]['Toa_vref'] = int(tot_vref_val)
        i2csocket.configure(yamlNode=nestedConf.to_dict())
        i2csocket.sipm_configure_injection(injectedChannels, activate=1, gain=gain_tot, calib_dac=calib_dac_val)
        util.acquire_scan(daq=daqsocket)
        chip_params = {'Toa_vref' : tot_vref_val,'injectedChannels':injectedChannels[0]}
        util.saveMetaYaml(odir=odir, i2c=i2csocket, daq=daqsocket, runid=index, testName=testName, keepRawData=keepRawData, chip_params=chip_params)
        index = index + 1
    i2csocket.sipm_configure_injection(injectedChannels, activate=0, gain=0, calib_dac=0) #maybe we should go back to phase 0
    return

def scan_trimToa(i2csocket, daqsocket, odir,chan,gain_tot=0,calib_dac_val=1800,keepRawData=0):
    testName = 'toa_trim_scan'
    trim_toa_vals = [i for i in range(0,64,1)]
    injectedChannels = [chan,chan+36]
    index=0
    for trim_toa_val in trim_toa_vals:
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys():
            if key.find('roc_s')==0:
                nestedConf[key]['sc']['ch'][chan]['trim_toa']=trim_toa_val
                # nestedConf[key]['sc']['ch'][chan+18]['trim_tot']=trim_tot_val
                nestedConf[key]['sc']['ch'][chan+36]['trim_toa']=trim_toa_val
                # nestedConf[key]['sc']['ch'][chan+36+18]['trim_tot']=trim_tot_val
        i2csocket.configure(yamlNode=nestedConf.to_dict())
        i2csocket.sipm_configure_injection(injectedChannels, activate=1, gain=gain_tot, calib_dac=calib_dac_val)
        util.acquire_scan(daq=daqsocket)
        chip_params = { 'trim_tot': trim_toa_val, 'injectedChannels':injectedChannels[0]}
        util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,runid=index,testName=testName,keepRawData=keepRawData,chip_params=chip_params)
        index+=1
    i2csocket.sipm_configure_injection(injectedChannels, activate=0, gain=0, calib_dac=0) #maybe we should go back to phase 0
    return


def toa_threshold_scan_sipm(i2csocket, daqsocket, clisocket, basedir, device_name, injectionConfig, suffix=''):
    if type(i2csocket) != zmqctrl.i2cController :
        print("ERROR in pedestal_run : i2csocket should be of type %s instead of %s"%(zmqctrl.i2cController,type(i2csocket)))
        sleep(1)
        return

    if type(daqsocket) != zmqctrl.daqController :
        print("ERROR in pedestal_run : daqsocket should be of type %s instead of %s"%(zmqctrl.daqController,type(daqsocket)))
        sleep(1)
        return	

    if type(clisocket) != zmqctrl.daqController :
        print("ERROR in pedestal_run : clisocket should be of type %s instead of %s"%(zmqctrl.daqController,type(clisocket)))
        sleep(1)
        return
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if suffix:
        timestamp = timestamp + "_" + suffix
    odir = "%s/%s/toa_threshold_scan/run_%s/"%(os.path.realpath(basedir), device_name, timestamp)
    os.makedirs(odir)
    
    ########### Configuration:
    chan_range = injectionConfig['chan_range']
    _0_set_trimtot31 = True # set all trim_tot of all channels = 31
    _0_find_Max_calib = True #True
    _1_set_tot_vref = True #True #True
    _2_set_trim_tot = False
    _3_calib_detect_minCharge = False
    adc_min = 950 # ADC target for TOT trigger
    gain_tot = 1
    bestch = 2 
    calib2V5_total = [i for i in range(300,1500,5)]
    toa_vref_min = 170   #i for i in range(170,270,2
    toa_vref_max = 270
    toa_vref_step = 2
    NEvents = 100
    calib2V5_total_final = [i for i in range(0,400,50)] + [i for i in range(400,700,2)] + [i for i in range(700,4096,50)]
        
    ###############################################

    #####  Setting trim_tot for all channels to 31
    if _0_set_trimtot31 == True:
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys():
            if key.find('roc_s')==0:
                nestedConf[key]['sc']['ch']['all']['trim_tot']=31
                nestedConf[key]['sc']['cm']['all']['trim_tot']=31
                nestedConf[key]['sc']['calib']['all']['trim_tot']=31
        i2csocket.configure(yamlNode=nestedConf.to_dict())

    #####  0. Find calib_2V5 value for MAX ADC before saturation:
    # (gainconv=15 -> ~190 calib, gainconv=4 -> ~720calib
    if _0_find_Max_calib == True:
        injectedChannels = [bestch,bestch+36]
        injectionConfig = {
            'BXoffset' : 22, #19
            'gain' : gain_tot,
            'calib' : [i for i in calib2V5_total],
            'injectedChannels' : injectedChannels
        }
        odir_inj = "%s/%s/"%(os.path.realpath(basedir), device_name)
        dut_inj = "tot_threshold_scan/run_%s/0_injection_scan/"%(timestamp)
        sipm_injection_scan_conv_mat_TB_23_08.sipm_injection_scan(i2csocket,daqsocket,clisocket,odir_inj,dut_inj,injectionConfig,suffix="gain%i_ch%i"%(gain_tot,bestch),keepRawData=1,analysis=1)

        odir_specific = "%s/%s/injection_scan/"%(odir_inj, dut_inj)
        tot_threshold_analyzer = analyzer.tot_scan_analyzer(odir=odir_specific)
        folders = glob.glob(odir_specific+"run_*/")
        df_ = []
        for folder in folders:
            files = glob.glob(folder+"/*.root")
            for f in files[:]:
                df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
                df_raw = uproot3.open(f)['unpacker_data']['hgcroc'].pandas.df()
                df_raw['Calib'] = df_summary.Calib.unique()[0]
                df_raw['channeltype'] = df_summary.channeltype.copy()
                df_raw['injectedChannels'] = df_summary.injectedChannels.unique()[0]
                df_raw['gain'] = df_summary.gain.unique()[0]
                df_.append(df_raw)
        tot_threshold_analyzer.data = pandas.concat(df_)
        # Keep minimum calib value for rest of the test
        calib_for_MaxADC = tot_threshold_analyzer.makePlot_calib_for_MaxADC(adc_min=adc_min)
        del tot_threshold_analyzer
        
        print("#######")
        print("calib_for_maxadc {}".format(calib_for_MaxADC))
        print("#######")        

    ###############################################
    #####  1. Scan tot_vref
    if _1_set_tot_vref == True:
        for ch in chan_range:
            rundir = odir + "1_start_chan_%i" %ch
            os.makedirs(rundir)
            mylittlenotifier = myinotifier.mylittleInotifier(odir=rundir)
            mylittlenotifier.start()
            
            #calib_for_MaxADC = 640 #injected channel = 2
            
            calibreqA = 0x10
            BXoffset = injectionConfig['BXoffset']

            clisocket.yamlConfig['client']['outputDirectory'] = rundir
            clisocket.yamlConfig['client']['run_type'] = "tot_threshold_scan"
            clisocket.yamlConfig['client']['serverIP'] = daqsocket.ip
            clisocket.configure()

            daqsocket.yamlConfig['daq']['active_menu']='calibAndL1A'
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['NEvents']=100
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxCalib']=calibreqA
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxL1A']=calibreqA+BXoffset
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthCalib']=1
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthL1A']=1
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['prescale']=0
            daqsocket.configure()

            util.saveFullConfig(odir=rundir,i2c=i2csocket,daq=daqsocket,cli=clisocket)
            
            if ch == chan_range[0]:
                util.saveFullConfig(odir=odir, i2c=i2csocket, daq=daqsocket, cli=clisocket)
            clisocket.start()
            injectedChannels = [ch,ch+36]
            scan_tot_vref(i2csocket, daqsocket, tot_vref_min, tot_vref_max, tot_vref_step, injectedChannels, rundir,gain_tot=gain_tot,calib_dac_val=calib_for_MaxADC,keepRawData=1)
            clisocket.stop()
            mylittlenotifier.stop()
        
        tot_threshold_analyzer = analyzer.tot_scan_analyzer(odir=odir)
        folders = glob.glob(odir+"1_start_chan_*/")
        df_ = []
        for folder in folders:
            files = glob.glob(folder+"/*.root")
            for f in files[:]:
                df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
                df_raw = uproot3.open(f)['unpacker_data']['hgcroc'].pandas.df()
                df_raw['Tot_vref'] = df_summary.Tot_vref.unique()[0]
                df_raw['injectedChannels'] = df_summary.injectedChannels.unique()[0]
                chan_uniq = df_summary.injectedChannels.unique()[0]
                df_raw = df_raw[df_raw.channel.isin([chan_uniq,chan_uniq+36])].copy()
                df_.append(df_raw)
        tot_threshold_analyzer.data = pandas.concat(df_)
        tot_threshold_analyzer.makePlot(preffix="1")
        tot_threshold_analyzer.determineTot_vref(correction_totvref=0)
        i2csocket.update_yamlConfig(fname=odir+'/tot_vref.yaml')
        i2csocket.configure(fname=odir+'/tot_vref.yaml')

        del tot_threshold_analyzer

    ## 2. Trimmed_dac scan ####################################################
    if _2_set_trim_tot == True:
        for ch in chan_range:
            rundir = odir + "2_chan_%i" %ch
            os.makedirs(rundir)
            mylittlenotifier = myinotifier.mylittleInotifier(odir=rundir)
            mylittlenotifier.start()
            
            #calib_for_MaxADC = 640 #injected channel = 2
            
            calibreqA = 0x10
            BXoffset = injectionConfig['BXoffset']
            
            clisocket.yamlConfig['client']['outputDirectory'] = rundir
            clisocket.yamlConfig['client']['run_type'] = "tot_trim_scan"
            clisocket.yamlConfig['client']['serverIP'] = daqsocket.ip
            clisocket.configure()

            daqsocket.yamlConfig['daq']['active_menu']='calibAndL1A'
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['NEvents']=1000
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxCalib']=calibreqA
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['bxL1A']=calibreqA+BXoffset
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthCalib']=1
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['lengthL1A']=1
            daqsocket.yamlConfig['daq']['menus']['calibAndL1A']['prescale']=0
            daqsocket.configure()

            util.saveFullConfig(odir=rundir, i2c=i2csocket, daq=daqsocket, cli=clisocket)           
            if ch == chan_range[0]:
                util.saveFullConfig(odir=odir, i2c=i2csocket, daq=daqsocket, cli=clisocket)
            clisocket.start()

            scan_trimTot(i2csocket, daqsocket,rundir,ch,gain_tot=gain_tot,calib_dac_val=calib_for_MaxADC,keepRawData=1)
            clisocket.stop()
            mylittlenotifier.stop()

        tot_trim_analyzer = analyzer.tot_scan_analyzer(odir=odir)
        folders = glob.glob(odir+"2_chan_*/")
        df_ = []
        for folder in folders:
            files = glob.glob(folder+"/*.root")
            for f in files[:]:
                df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
                df_raw = uproot3.open(f)['unpacker_data']['hgcroc'].pandas.df()
                df_raw['trim_tot'] = df_summary.trim_tot.unique()[0]
                df_raw['injectedChannels'] = df_summary.injectedChannels.unique()[0]
                chan_uniq = df_summary.injectedChannels.unique()[0]
                df_raw = df_raw[df_raw.channel.isin([chan_uniq,chan_uniq+36])].copy()
                df_.append(df_raw)
        tot_trim_analyzer.data = pandas.concat(df_)
        tot_trim_analyzer.makePlot_trim(preffix="2")
        tot_trim_analyzer.determineTot_trim(correction_tottrim=0)
        i2csocket.update_yamlConfig(fname=odir+'/trimmed_tot.yaml')
        i2csocket.configure(fname=odir+'/trimmed_tot.yaml')

        del tot_trim_analyzer

    ##### Look for minimum charge with TOT data
    if _3_calib_detect_minCharge == True:
        print(" ############## Start injection scan #################")
        for chan in chan_range:
            injectedChannels = [chan,chan+36]
            injectionConfig = {
                'BXoffset' : 22, #19
                'gain' : gain_tot,
                'calib' : [i for i in calib2V5_total_final],
                'injectedChannels' : injectedChannels
            }
            odir_inj = "%s/%s/"%(os.path.realpath(basedir), device_name)
            dut_inj = "tot_threshold_scan/run_%s/"%(timestamp)
            sipm_injection_scan_conv_mat_TB_23_08.sipm_injection_scan(i2csocket,daqsocket,clisocket,odir_inj,dut_inj,injectionConfig,suffix="gain%i_ch%i"%(gain_tot,chan),keepRawData=1,analysis=1)

        odir_specific = "%s/%s/injection_scan/"%(odir_inj, dut_inj)
        tot_threshold_analyzer = analyzer.tot_scan_analyzer(odir=odir_specific)
        folders = glob.glob(odir_specific+"run_*/")
        df_ = []
        for folder in folders:
            files = glob.glob(folder+"/*.root")
            for f in files[:]:
                df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
                df_raw = uproot3.open(f)['unpacker_data']['hgcroc'].pandas.df()
                df_raw['injectedChannels'] = df_summary.injectedChannels.unique()[0]
                df_raw['Calib'] = df_summary.Calib.unique()[0]
                df_raw['gain'] = df_summary.gain.unique()[0]
                chan_uniq = df_summary.injectedChannels.unique()[0]
                df_raw = df_raw[df_raw.channel.isin([chan_uniq,chan_uniq+36])].copy()
                df_.append(df_raw)
        tot_threshold_analyzer.data = pandas.concat(df_)
        tot_threshold_analyzer.makePlot_calib(NEvents=NEvents,config_ns_charge='pC')
        
        del tot_threshold_analyzer

    return odir
        
if __name__ == "__main__" :
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

    parser.add_option("-s", "--suffix",
                      action="store", dest="suffix",default='',
                      help="output base directory")
    
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
    
    parser.add_option("-I", "--initialize",default=False,
                      action="store_true", dest="initialize",
                      help="set to re-initialize the ROCs and daq-server instead of only configuring")

    (options, args) = parser.parse_args()
    print(options)
    if not options.hexaIP:
        options.hexaIP = '10.254.56.32'
        # was options.hexaIP = '129.104.89.111'
    print(options.hexaIP)

    daqsocket = zmqctrl.daqController(options.hexaIP, options.daqPort, options.configFile)
    clisocket = zmqctrl.daqController("localhost", options.pullerPort, options.configFile)
    i2csocket = zmqctrl.i2cController(options.hexaIP, options.i2cPort, options.configFile)
    
    injectionConfig = {
        'BXoffset' : 22,    #22 for ADC
        'chan_range' : range(0,3), #range(1),
        'phase' : 3,  # optimal value for tot threshold scans
    }

    i2csocket.configure()
    tot_threshold_scan_sipm(i2csocket, daqsocket, clisocket, options.odir, options.dut,injectionConfig,suffix="")
	






# import zmq, datetime,  os, subprocess, sys, yaml, glob
# from time import sleep

# import pandas
# from level0.analyzer import *
# import myinotifier,util
# #import analysis.level0.toa_scan_analysis as analyzer
# import analysis.level0.toa_scan_analysis_TB_23_08 as analyzer
# import zmq_controler as zmqctrl
# from nested_dict import nested_dict
# import sipm_injection_scan_conv_mat_TB_23_08


# def sipm_injection_scan(i2csocket,daqsocket,clisocket,basedir,device_name,injectionConfig,suffix='',keepRawData=1,analysis=1):
#     if type(i2csocket) != zmqctrl.i2cController:
#         print( "ERROR in pedestal_run : i2csocket should be of type %s instead of %s"%(zmqctrl.i2cController,type(i2csocket)) )
#         sleep(1)
#         return
    
#     if type(daqsocket) != zmqctrl.daqController:
#         print( "ERROR in pedestal_run : daqsocket should be of type %s instead of %s"%(zmqctrl.daqController,type(daqsocket)) )
#         sleep(1)
#         return
    
#     if type(clisocket) != zmqctrl.daqController:
#         print( "ERROR in pedestal_run : clisocket should be of type %s instead of %s"%(zmqctrl.daqController,type(clisocket)) )
#         sleep(1)
#         return
    
#     timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#     if suffix:
#         timestamp = timestamp + "_" + suffix
#     odir = "%s/%s/injection_scan/run_%s/"%( os.path.realpath(basedir), device_name, timestamp ) # a complete path is needed
#     os.makedirs(odir)
    
#     #calib2V5_total = [i for i in range(100,1150,25)]
#     calib2V5_total = [i for i in range(200,600,10)]
#     #injectedChannels = range(0, 36)#, 5)
#     injectedChannels = [20, 22, 33, 35, 29, 31, 24, 26, 19, 21, 32, 34,
#     28, 30, 23, 25, 14, 16, 10, 12, 1, 3, 5, 7, 13, 15, 9, 11, 0, 2, 4, 6]
    
#     #injectedChannels = [32]
    
#     #injectedChannels = range(0, 6)
#     #injectedChannels = range(6, 12)
#     #injectedChannels = range(12, 18)
#     #injectedChannels = range(18, 24)
#     #injectedChannels = range(24, 30)
#     #injectedChannels = range(30, 36)
   
    
    
#     gain=0
#     injection_scan_mode=1
    
#     if injection_scan_mode == 1:
#         print(" ############## Start injection scan #################")
#         for injChannel in injectedChannels:
#             injectionConfig = {
#             'BXoffset' : 22, # was 22
#             'gain' : gain,
#             'calib' : [i for i in calib2V5_total],
#             'injectedChannels' : [injChannel, injChannel + 36]
#             }
#             sipm_injection_scan_conv_mat_TB_23_08.sipm_injection_scan(i2csocket,daqsocket,clisocket,options.odir,options_dut,injectionConfig,suffix="gain0_ch%i"%injChannel,keepRawData=1,analysis=1)

#         odir = "%s/%s/injection_scan/"%(options.odir, options_dut)
#         toa_threshold_analyzer = analyzer.toa_scan_analyzer(odir=odir)
#         folders = glob.glob(odir+"run_*/")
#         df_ = []
#         for folder in folders:
#                 files = glob.glob(folder+"/*.root")
#                 for f in files[:]:
#                         df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
#                         df_.append(df_summary)
#         toa_threshold_analyzer.data = pandas.concat(df_)
#         toa_threshold_analyzer.makePlot_calib(config_ns_charge='pC', thres=0.95)
#         #toa_threshold_analyzer.makePlot_calib(config_ns_charge='pC', thres=0.85)
#         #toa_threshold_analyzer.makePlot_calib(config_ns_charge='pC', thres=0.5)
        
#         del toa_threshold_analyzer
    
#      # do not run the inotifier if the unpacker is not yet ready to read vectors inside metaData yaml file using key "chip_params"
    


# if __name__ == "__main__":
#     from optparse import OptionParser
#     parser = OptionParser()
    
#     parser.add_option("-d", "--dut", dest="dut",
#                       help="device under test")
    
#     parser.add_option("-i", "--hexaIP",
#                       action="store", dest="hexaIP",
#                       help="IP address of the zynq on the hexactrl board")
    
#     parser.add_option("-f", "--configFile",default="./configs/init.yaml",
#                       action="store", dest="configFile",
#                       help="initial configuration yaml file")
    
#     parser.add_option("-s", "--suffix",
#                       action="store", dest="suffix",default='',
#                       help="output base directory")

#     parser.add_option("-o", "--odir",
#                       action="store", dest="odir",default='./data',
#                       help="output base directory")
    
#     parser.add_option("--daqPort",
#                       action="store", dest="daqPort",default='6000',
#                       help="port of the zynq waiting for daq config and commands (configure/start/stop/is_done)")
    
#     parser.add_option("--i2cPort",
#                       action="store", dest="i2cPort",default='5555',
#                       help="port of the zynq waiting for I2C config and commands (initialize/configure/read_pwr,read/measadc)")
    
#     parser.add_option("--pullerPort",
#                       action="store", dest="pullerPort",default='6001',
#                       help="port of the client PC (loccalhost for the moment) waiting for daq config and commands (configure/start/stop)")
    
#     parser.add_option("-I", "--initialize",default=False,
#                       action="store_true", dest="initialize",
#                       help="set to re-initialize the ROCs and daq-server instead of only configuring")
    
#     (options, args) = parser.parse_args()
#     print(options)
#     if not options.hexaIP:
#         options.hexaIP = '10.254.56.32'
#         # was options.hexaIP = '129.104.89.111'
#     print(options.hexaIP)

#     ############    
#     # SUFFIX CONFIG:
#     timestamp_fulltest = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#     if options.suffix == None:
#         options_dut = options.dut + "/vreftoa_scurvescan/test_%s"%(timestamp_fulltest)
#     else:
#         options_dut = options.dut + "/vreftoa_scurvescan/test_%s_%s"%(timestamp_fulltest, options.suffix)
#     #print(" ############## options_dut = ",options_dut ," #################")
#     ############
    
#     daqsocket = zmqctrl.daqController(options.hexaIP,options.daqPort,options.configFile)
#     clisocket = zmqctrl.daqController("localhost",options.pullerPort,options.configFile)
#     i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort,options.configFile)
    
#     if options.initialize==True:
#         i2csocket.initialize()
#         clisocket.yamlConfig['client']['serverIP'] = daqsocket.ip
#         clisocket.initialize()
#         daqsocket.initialize()
#     else:
#         i2csocket.configure()

#     injectionConfig = {
#         'BXoffset' : 22,   # was 23
#         'gain' : 1,
#         'phase' : 6,   #was 7
#         # 'calib' : [-1]+[i for i in range(0,4000,100)],
#         'calib' : [i for i in range(0,500,50)],
#         'injectedChannels' : range(2)
#     }
#     sipm_injection_scan(i2csocket,daqsocket,clisocket,options.odir,options_dut,injectionConfig,suffix=options.suffix,keepRawData=0,analysis=1)
