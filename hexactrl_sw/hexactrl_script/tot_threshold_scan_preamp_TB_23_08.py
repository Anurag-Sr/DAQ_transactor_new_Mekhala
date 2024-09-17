import zmq, datetime,  os, subprocess, sys, yaml, glob
from time import sleep

from level0.analyzer import *
import myinotifier, util
import analysis.level0.tot_scan_analysis_TB_23_08 as analyzer
import zmq_controler as zmqctrl
from nested_dict import nested_dict
import numpy as np
import pandas
import miscellaneous_functions as misc_func
import injection_scan_int_preamp_0502 as inj_preamp

def scan_tot_vref(i2csocket, daqsocket, startthr, stopthr, nstep, injectedChannels,odir,gain_tot=0,calib_dac_val=1800,keepRawData=0) :
    testName = 'tot_threshold_scan'
    index = 0
    for tot_vref_val in range(startthr, stopthr, nstep) :
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys() :
            if key.find('roc_s') == 0 :
                nestedConf[key]['sc']['ReferenceVoltage'][0]['Tot_vref'] = int(tot_vref_val)
                nestedConf[key]['sc']['ReferenceVoltage'][1]['Tot_vref'] = int(tot_vref_val)
        i2csocket.configure(yamlNode=nestedConf.to_dict())
        
        i2csocket.configure_injection(trim_val = 0, process = 'int', calib_preamp = calib_dac_val, calib_conv = 0, gain=gain_tot,injectedChannels=injectedChannels, IntCtest = 0, choice_cinj = 0, cmd_120p = 1, L_g2 = 1, H_g2 = 1, L_g1 = 0, H_g1 = 1, L_g0 = 1, H_g0 = 0)    

        #i2csocket.sipm_configure_injection(injectedChannels, activate=1, gain=gain_tot, calib_dac=calib_dac_val)
        util.acquire_scan(daq=daqsocket)
        chip_params = {'Tot_vref' : tot_vref_val,'injectedChannels':injectedChannels[0]}
        util.saveMetaYaml(odir=odir, i2c=i2csocket, daq=daqsocket, runid=index, testName=testName, keepRawData=keepRawData, chip_params=chip_params)
        index = index + 1
    #i2csocket.sipm_configure_injection(injectedChannels, activate=0, gain=0, calib_dac=0) #maybe we should go back to phase 0
    i2csocket.configure_injection(trim_val = 0, process = 'int', calib_preamp = 0, calib_conv = 0, gain=0,injectedChannels=injectedChannels, IntCtest = 0, choice_cinj = 0, cmd_120p = 0, L_g2 = 1, H_g2 = 1, L_g1 = 0, H_g1 = 1, L_g0 = 1, H_g0 = 0)    

    return

def scan_trimTot(i2csocket, daqsocket, odir,chan,gain_tot=0,calib_dac_val=1800,keepRawData=0):
    testName = 'tot_trim_scan'
    trim_tot_vals = [i for i in range(0,64,1)]
    injectedChannels = [chan,chan+36]
    index=0
    for trim_tot_val in trim_tot_vals:
        nestedConf = nested_dict()
        for key in i2csocket.yamlConfig.keys():
            if key.find('roc_s')==0:
                nestedConf[key]['sc']['ch'][chan]['trim_tot']=trim_tot_val
                # nestedConf[key]['sc']['ch'][chan+18]['trim_tot']=trim_tot_val
                nestedConf[key]['sc']['ch'][chan+36]['trim_tot']=trim_tot_val
                # nestedConf[key]['sc']['ch'][chan+36+18]['trim_tot']=trim_tot_val
        i2csocket.configure(yamlNode=nestedConf.to_dict())
        
        i2csocket.configure_injection(trim_val = 0, process = 'int', calib_preamp = calib_dac_val, calib_conv = 0, gain=gain_tot,injectedChannels=injectedChannels, IntCtest = 0, choice_cinj = 0, cmd_120p = 1, L_g2 = 1, H_g2 = 1, L_g1 = 0, H_g1 = 1, L_g0 = 1, H_g0 = 0)    

        #i2csocket.sipm_configure_injection(injectedChannels, activate=1, gain=gain_tot, calib_dac=calib_dac_val)
        util.acquire_scan(daq=daqsocket)
        chip_params = { 'trim_tot':trim_tot_val, 'injectedChannels':injectedChannels[0]}
        util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,runid=index,testName=testName,keepRawData=keepRawData,chip_params=chip_params)
        index+=1
    #i2csocket.sipm_configure_injection(injectedChannels, activate=0, gain=0, calib_dac=0) #maybe we should go back to phase 0
    i2csocket.configure_injection(trim_val = 0, process = 'int', calib_preamp = 0, calib_conv = 0, gain=0,injectedChannels=injectedChannels, IntCtest = 0, choice_cinj = 0, cmd_120p = 0, L_g2 = 1, H_g2 = 1, L_g1 = 0, H_g1 = 1, L_g0 = 1, H_g0 = 0)    

    return


def tot_threshold_scan_sipm(i2csocket, daqsocket, clisocket, basedir, device_name, injectionConfig, suffix=''):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if suffix:
        timestamp = timestamp + "_" + suffix
    odir = "%s/%s/tot_threshold_scan/run_%s/"%(os.path.realpath(basedir), device_name, timestamp)
    os.makedirs(odir)
    
    ########### Configuration:
    chan_range = injectionConfig['chan_range']
    _0_set_trimtot31 = True     # set all trim_tot of all channels = 31
    _0_find_Max_calib = True    # Do a calib scan into the current conveyer to find the calib value for a given ADC target.
    _1_set_tot_vref = False      # Performs a tot_vref scan in all channels selected from the 'chan_range' variable and save the tot_vref value
    _2_set_trim_tot = False     # Performs a trim_tot scan in all channels selected from the 'chan_range' variable and save the tot_vref value
    #_2_set_trim_tot = True     # Performs a trim_tot scan in all channels selected from the 'chan_range' variable and save the tot_vref value
    
    _3_calib_detect_minCharge = False # Do a calib scan into the current conveyer to detect the min charge with all events with TOT data.
    adc_min = 1000 # was 950              # defines the ADC target for the TOT trigger
    gain_tot = 1 # was 1                # defines the gain (0 or 1) of the injection to find the calib value
    bestch = 4                  # defines one channel chosen to do this injection scan
    #calib2V5_total = [i for i in range(400,1500,5)] # calib values for the injection scan into the current conveyer
    calib2V5_total = [i for i in range(0,2000,25)] # calib values for the injection scan into the current conveyer
    tot_vref_min = 300  # was 400 below 300 looks unsafe        # start tot_vref value for the scan
    tot_vref_max = 500  # was 700       # end tot_vref value for the scan
    tot_vref_step = 5           # step tot_vref value for the scan
    NEvents = 100               # needs the same number of events as in the injection_scan script.
    #calib2V5_total_final = [i for i in range(0,400,50)] + [i for i in range(400,700,2)] + [i for i in range(700,4096,50)] # calib values for the injection scan into the current conveyer
    calib2V5_total_final = [i for i in range(0,200,2)] + [i for i in range(200,1000,20)] # calib values for the injection scan into the current conveyer    
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
        testName = "tot_global_scan"
        odir = misc_func.mkdir(os.path.realpath(basedir),options.device_type,testName = testName,suffix=suffix)
    
        for ch in chan_range:
            injectedChannels = [ch,ch+36]
            injectionConfig = {
                'BXoffset' : 21, #19
                'gain' : gain_tot,
                'calib' : [i for i in calib2V5_total],
                'injectedChannels' : injectedChannels,
                'phase': 15
            }            
            
            inj_preamp.sipm_injection_scan(i2csocket,daqsocket,clisocket,odir,options.dut,options.device_type, injectionConfig,scurve_scan = 1,suffix="gain0_ch%i"%bestch,active_menu = 'calibAndL1AplusTPG',keepRawData=1,analysis=1)
            
            '''
            #odir_specific = "/home/hgcal/Desktop/Tileboard_DAQ_GitLab_version_2024/DAQ_transactor_new/hexactrl-sw/hexactrl-script/data/TB3/tot_threshold_scan/run_20240705_144249/0_injection_scan/injection_scan/"
            tot_threshold_analyzer = analyzer.tot_scan_analyzer(odir=odir)
            #folders = glob.glob(odir_specific+"run_*/")
            folders = glob.glob(odir+"PreampInjection_scan_*/")
            df_ = []
            for folder in folders:
                files = glob.glob(folder+"/*.root")
                for f in files[:]:
                    df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
                    df_raw = uproot3.open(f)['unpacker_data']['hgcroc'].pandas.df()
                    df_raw['Calib'] = df_summary.Calib.unique()[0]
                    #df_raw['channeltype'] = df_summary['channeltype']
                    #df_raw['channeltype'] = df_summary.channeltype.copy()
                    df_raw['injectedChannels'] = df_summary.injectedChannels.unique()[0]
                    df_raw['gain'] = df_summary.gain.unique()[0]
                    df_.append(df_raw)
            tot_threshold_analyzer.data = pandas.concat(df_)

            # Keep minimum calib value for rest of the test
            calib_for_MaxADC = tot_threshold_analyzer.makePlot_calib_for_MaxADC(adc_min=adc_min) # In this line, this variable is saved and kept for the rest of the script as the calib value for the ADC target.
            del tot_threshold_analyzer

            print("#######")
            print("calib_for_maxadc {}".format(calib_for_MaxADC))
            print("#######")        
            '''


        tot_threshold_analyzer = analyzer.tot_scan_analyzer(odir=odir)
        #folders = glob.glob(odir_specific+"run_*/")
        folders = glob.glob(odir+"PreampInjection_scan_*/")

        df_sum = []
        for folder in folders:
            files = glob.glob(folder+"/*.root")
            for f in files[:]:
                df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
                df_sum.append(df_summary)

        tot_threshold_analyzer.data_sum = pandas.concat(df_sum)
                 
        turn_avg_0,turn_avg_1,chan_0,chan_1 = tot_threshold_analyzer.calc_turnover([],0)
        print("turn over values for the current global tot")
        print("Half 0", turn_avg_0)
        print("Half_1", turn_avg_1)
        
        print("Channels closest to the average turnover value for each half") #These are the only channels that will be used for toa vref scan, because if more are used in the high range it will shift the turnover points, and therefore change the slopes and hence the tot values for a particular target
        print("Half 0", chan_0)
        print("Half_1", chan_1)
            
        del tot_threshold_analyzer            
            

    ###############################################
    #####  1. Scan tot_vref
    if _1_set_tot_vref == True:
        for ch in chan_range:
            rundir = odir + "1_start_chan_%i" %ch
            os.makedirs(rundir)
            mylittlenotifier = myinotifier.mylittleInotifier(odir=rundir)
            mylittlenotifier.start()
            
            calib_for_MaxADC = 690 #injected channel = 2
            
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

            util.saveFullConfig(odir=rundir,i2c=i2csocket,daq=daqsocket,cli=clisocket,filename = 'initial_full_config.yaml')
            
            if ch == chan_range[0]:
                util.saveFullConfig(odir=odir, i2c=i2csocket, daq=daqsocket, cli=clisocket,filename = 'initial_full_config.yaml')
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
            
            calib_for_MaxADC = 690 #injected channel = 2
            
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

            util.saveFullConfig(odir=rundir, i2c=i2csocket, daq=daqsocket, cli=clisocket,filename = 'initial_full_config.yaml')           
            if ch == chan_range[0]:
                util.saveFullConfig(odir=odir, i2c=i2csocket, daq=daqsocket, cli=clisocket,filename = 'initial_full_config.yaml')
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
            inj_preamp.sipm_injection_scan(i2csocket,daqsocket,clisocket,odir_inj,dut_inj,injectionConfig,suffix="gain%i_ch%i"%(gain_tot,chan),keepRawData=1,analysis=1)

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
    parser = misc_func.options_run()#This will be constant for every test irrespective of the type of test
    
    (options, args) = parser.parse_args()
    print(options)
    (daqsocket,clisocket,i2csocket) = zmqctrl.pre_init(options)
    
    injectionConfig = {
        'BXoffset' : 22,    #22 for ADC
        'chan_range' : range(0, 36), #range(1),
        'phase' : 3,  # optimal value for tot threshold scans. was 3 
    }
    
    tot_threshold_scan_sipm(i2csocket, daqsocket, clisocket, options.odir, options.dut,injectionConfig,suffix="")
	
