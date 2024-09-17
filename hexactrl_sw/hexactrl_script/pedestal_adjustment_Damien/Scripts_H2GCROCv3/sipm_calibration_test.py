import yaml, datetime, os, sys, glob  #,paramiko
from time import sleep, time
import numpy as np

import zmq_controler as zmqctrl

import pedestal_run
import vrefinv_scan
import vrefnoinv_scan
import pedestal_scan
import sipm_sampling_scan
import toa_threshold_scan_sipm
import tot_threshold_scan_sipm
# import adc_range_setting
# import adc_range_setting_sipm
# import agilent_ctrl
from nested_dict import nested_dict 

#  script to calibrate the chip
# Example: 
# source opt/hexactrl/ROCv3-dev-WIP/ctrl/etc/env.sh
# python3 sipm_calibration_test.py -d roc0_sipm_v3 -f configs/sipm_init1ROC.yaml --gain_conv 12 -r 0 -I (Just the first time)
# python3 sipm_calibration_test.py -d roc0_sipm_v3 -f configs/sipm_init1ROC.yaml --gain_conv 12 -r 0

if __name__ == "__main__":
    ############ CONFIG ############
    ch = 10 #17
    ################################

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

    parser.add_option("-p", "--prologixIP",default="",
                      action="store", dest="prologixIP",
                      help="IP address of the prologix gpib ethernet controller, if not defined: the script will skip all agilent related commands")

    parser.add_option("-g", "--gpibAddress",default=5,type=int,
                      action="store", dest="gpibAddress",
                      help="gpib address set on the agilent PSU")

    parser.add_option("--gain_conv",default=15,type=int,
                      action="store", dest="gain_conv",
                      help="gpib address set on the agilent PSU")

    # parser.add_option("--ONbackup",default=0,type=int,
    #                   action="store", dest="ONbackup",
    #                   help="ONbackup=0 enable compensation with common mode channel")

    parser.add_option("-r", "--roc_asic",default='0',
                      action="store", dest="roc_asic",
                      help="roc asic number")

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
    start = time() 

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
    
    print(" ############## Starting up the MASTER TDCs #################")
    nestedConf = nested_dict()
    for key in i2csocket.yamlConfig.keys():
        if key.find('roc_s')==0:
            nestedConf[key]['sc']['MasterTdc']['all']['EN_MASTER_CTDC_VOUT_INIT']=1
            nestedConf[key]['sc']['MasterTdc']['all']['VD_CTDC_P_DAC_EN']=1
            nestedConf[key]['sc']['MasterTdc']['all']['VD_CTDC_P_D']=16
            nestedConf[key]['sc']['MasterTdc']['all']['EN_MASTER_FTDC_VOUT_INIT']=1
            nestedConf[key]['sc']['MasterTdc']['all']['VD_FTDC_P_DAC_EN']=1
            nestedConf[key]['sc']['MasterTdc']['all']['VD_FTDC_P_D']=16
    i2csocket.update_yamlConfig(yamlNode=nestedConf.to_dict())
    i2csocket.configure()
    nestedConf = nested_dict()
    for key in i2csocket.yamlConfig.keys():
        if key.find('roc_s')==0:
            nestedConf[key]['sc']['MasterTdc']['all']['EN_MASTER_CTDC_VOUT_INIT']=0
            nestedConf[key]['sc']['MasterTdc']['all']['EN_MASTER_FTDC_VOUT_INIT']=0
    i2csocket.update_yamlConfig(yamlNode=nestedConf.to_dict())
    i2csocket.configure()

    #config_file_odir = "%s/%s/trimmed_device.yaml" %(os.path.realpath(options.odir), options.dut)
    roc_asic = options.roc_asic
    # ONbackup = options.ONbackup
    ONbackup = 0
    gain_conv = options.gain_conv
    config_file_odir = "./configs/sipm_roc%s_onbackup%i_gainconv%i.yaml"%(roc_asic, ONbackup, gain_conv)

    print(" ############## Starting conf ONbackup=%i, Gain_conv=%i #################" %(ONbackup,gain_conv))
    nestedConf = nested_dict()
    for key in i2csocket.yamlConfig.keys():
        if key.find('roc_s')==0:
            if gain_conv > 7:
                nestedConf[key]['sc']['GlobalAnalog'][0]['Gain_conv'] = 8
                nestedConf[key]['sc']['GlobalAnalog'][1]['Gain_conv'] = 8
                nestedConf[key]['sc']['ch']['all']['Gain_conv'] = gain_conv - 8
            else:
                nestedConf[key]['sc']['GlobalAnalog'][0]['Gain_conv'] = 0
                nestedConf[key]['sc']['GlobalAnalog'][1]['Gain_conv'] = 0
                nestedConf[key]['sc']['ch']['all']['Gain_conv'] = gain_conv
            nestedConf[key]['sc']['GlobalAnalog'][0]['ON_backup'] = ONbackup
            nestedConf[key]['sc']['GlobalAnalog'][1]['ON_backup'] = ONbackup
    i2csocket.update_yamlConfig(yamlNode=nestedConf.to_dict())
    i2csocket.configure()
    suffix_newped = options.suffix + "_gainconv" + str(gain_conv)

    pedestal_run.pedestal_run(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix+"_default")

    ##########    Pedestal scan
    pedestal_scan.pedestal_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix)
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)    
    pedestal_run.pedestal_run(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix+"_default_trimmed")

    ##########    Setting Vref_inv to optimize the ADC dynamic range (Vref_noinv = 850)
    vrefinv_scan.vrefinv_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix)
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)
    pedestal_scan.pedestal_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix)
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)    
    vrefinv_conf_dir = pedestal_run.pedestal_run(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix+"_trimmed_vrefinv")
    i2csocket.update_yamlConfig(fname=vrefinv_conf_dir+'/ADC_pedestal.yaml') 
    i2csocket.configure(fname=vrefinv_conf_dir+'/ADC_pedestal.yaml')
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)

    ##########    Setting Vref_noinv to optimize the ADC dynamic range
    vrefnoinv_scan.vrefnoinv_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix)
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)
    pedestal_scan.pedestal_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix)
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)    
    vrefnoinv_conf_dir = pedestal_run.pedestal_run(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.suffix+"_trimmed_vrefnoinv")
    i2csocket.update_yamlConfig(fname=vrefnoinv_conf_dir+'/ADC_pedestal.yaml') 
    i2csocket.configure(fname=vrefnoinv_conf_dir+'/ADC_pedestal.yaml')
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)

    ##########    Determining the best Ref_dac_toa settings
    print("start toa_threshold_scan")
    # Check sampling scan and set best phase
    injectionConfig = {
    'gain' : 0,
        'calib' : 2000,
        'injectedChannels' : [ch,ch+36]
    }
    output_dir_bestphase = sipm_sampling_scan.sipm_sampling_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,injectionConfig,"test_before_toa_thr_set")
    i2csocket.update_yamlConfig(fname=output_dir_bestphase+'/best_phase.yaml') 
    i2csocket.configure(fname=output_dir_bestphase+'/best_phase.yaml')
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)
    phase = i2csocket.yamlConfig['roc_s0']['sc']['Top']['all']['phase_ck']
    l1a_offset = i2csocket.yamlConfig['roc_s0']['sc']['DigitalHalf'][0]['L1Offset']
    if phase in range(5):
        l1_val = 1
    else:
        l1_val = 0
    BXoffset = l1a_offset + 11 + l1_val  ## Calib_offset = 11
    injectionConfig = {
        'BXoffset' : BXoffset
        }
    toa_threshold_scan_sipm.toa_threshold_scan_sipm(i2csocket,daqsocket,clisocket,options.odir,options.dut,injectionConfig,suffix=options.suffix)
    with open(config_file_odir,'w') as fout:
        yaml.dump(i2csocket.yamlConfig,fout)

    ##########    Checking Toa_vref at the "lowest" values
    injectionConfig = {
    'gain' : 0,
        'calib' : 1000,
        'injectedChannels' : [ch,ch+36]
    }
    sipm_sampling_scan.sipm_sampling_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut,injectionConfig,"test_min_toa_thr")
    
    ###########    Determining the best Ref_dac_tot values   
    injectionConfig = {
        'BXoffset' : BXoffset
        }
    tot_threshold_scan_sipm.tot_threshold_scan_sipm(i2csocket,daqsocket,clisocket,options.odir,options.dut,injectionConfig,suffix=options.suffix)
    with open(config_file_odir,'w') as fout:
    
    end = time()
    print('Total test time: %f min' %((end-start)/60))

    
