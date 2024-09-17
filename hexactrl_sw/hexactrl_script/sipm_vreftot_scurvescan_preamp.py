import zmq, datetime,  os, subprocess, sys, yaml, glob
from time import sleep

import pandas
from level0.analyzer import *
import myinotifier,util
#import analysis.level0.tot_scan_analysis as analyzer
#import analysis.level0.tot_scan_analysis_TB_23_08 as analyzer
import zmq_controler as zmqctrl
from nested_dict import nested_dict
import miscellaneous_functions as misc_func
import injection_scan_int_preamp_0502 as inj_preamp


def sipm_injection_scan(i2csocket,daqsocket,clisocket,basedir,device_name,device_type,suffix='',keepRawData=1,analysis=1):
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if suffix:
        timestamp = timestamp + "_" + suffix
    #odir = "%s/%s/injection_scan/run_%s/"%( os.path.realpath(basedir), device_name, timestamp ) # a complete path is needed
    #os.makedirs(odir)
    
    
    injectedChannels = range(0, 36)
       
    #gain=0 #Of course this was originally for conveyor injection, but maybe it would be more beneficial for preamp injection if it is set to 1 (high range instead of low range)
    injection_scan_mode=1
    '''
    preamp_sampling_scan_phase_dir = '/home/hgcal/Desktop/Tileboard_DAQ_GitLab_version_2024/DAQ_transactor_new/hexactrl-sw/hexactrl-script/data/TB3/TB3_D8_11/PreampSampling_scan_Calib_200_TB3_D8_11_14/'
    with open(preamp_sampling_scan_phase_dir+'/best_phase.yaml','r+') as fin:
        BX_phase_info = yaml.safe_load(fin)   
    '''
    
    len_batch = 36
    #len_batch = 6
    if injection_scan_mode == 1:
        print(" ############## Start injection scan #################")
        for batch_num in range(int(len(injectedChannels)/len_batch)):
            inj_batch = []
            for channel in range(len_batch):
                cur_chan = batch_num*len_batch+channel
                inj_batch.append(cur_chan)
                inj_batch.append(cur_chan+ 36)
            injectionConfig = {
            #High range max phase for 6 injected channels
            #'BXoffset' : 22, # was 22
            #'phase' : 1,
            #'gain' : 1,
            
            #Low range max phase for 6 injected channels
            'BXoffset' : 21, # was 22
            'phase' : 12,
            
            'gain' : 0,
            'calib' : [i for i in range(100,4000,20)],
            #'injectedChannels' : [injChannel, injChannel + 36]
            'injectedChannels' : inj_batch
            }
            print("Batch number", batch_num)
            print("Injected channels", inj_batch)
            #print("Directories",odir,options.odir)
            inj_preamp.sipm_injection_scan(i2csocket,daqsocket,clisocket,options.odir,options_dut,device_type, injectionConfig,scurve_scan = 0,suffix="gain0_ch%i"%batch_num,active_menu = 'calibAndL1AplusTPG',keepRawData=1,analysis=1)
            
        '''
        odir = "%s/%s/injection_scan/"%(options.odir, options_dut)
        tot_threshold_analyzer = analyzer.tot_scan_analyzer(odir=odir)
        folders = glob.glob(odir+"run_*/")
        df_ = []
        for folder in folders:
                files = glob.glob(folder+"/*.root")
                for f in files[:]:
                        df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
                        df_.append(df_summary)
        tot_threshold_analyzer.data = pandas.concat(df_)
        tot_threshold_analyzer.makePlot_calib(config_ns_charge='pC', thres=0.95)
        #tot_threshold_analyzer.makePlot_calib(config_ns_charge='pC', thres=0.85)
        #tot_threshold_analyzer.makePlot_calib(config_ns_charge='pC', thres=0.5)
        
        del tot_threshold_analyzer
        '''
     # do not run the inotifier if the unpacker is not yet ready to read vectors inside metaData yaml file using key "chip_params"
    


if __name__ == "__main__":
    parser = misc_func.options_run()#This will be constant for every test irrespective of the type of test
    
    (options, args) = parser.parse_args()
    print(options)
    (daqsocket,clisocket,i2csocket) = zmqctrl.pre_init(options)

    ############    
    # SUFFIX CONFIG:
    timestamp_fulltest = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if options.suffix == None:
        options_dut = options.dut + "/vreftot_scurvescan/test_%s"%(timestamp_fulltest)
    else:
        options_dut = options.dut + "/vreftot_scurvescan/test_%s_%s"%(timestamp_fulltest, options.suffix)
    #print(" ############## options_dut = ",options_dut ," #################")
    ############
    
    sipm_injection_scan(i2csocket,daqsocket,clisocket,options.odir,options_dut,options.device_type,suffix=options.suffix,keepRawData=0,analysis=1)
