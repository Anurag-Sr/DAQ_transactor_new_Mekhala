import yaml, datetime, os, paramiko
import numpy as np

import zmq_controler as zmqctrl

import marspedestal_run
import marsvrefinv_scan
import marsvrefnoinv_scan
import marsphase_scan
import marspedestal_scan
from nested_dict import nested_dict

# Example: 
# python3 mars_prodtest.py -d hb -i hexactrlIP -f configs/initLD.yaml 
#

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
    
    # ssh_client = paramiko.SSHClient()
    # ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh_client.connect(options.hexaIP, username="root", password="centos")
    # stdin, stdout, stderr = ssh_client.exec_command("fw-loader load hexaboard-hd-tester-v1p1-trophy-v2; ")
    # print( "stderr: ", stderr.readlines() )
    # print( "pwd: ", stdout.readlines() )
    # from time import sleep
    # sleep(0.5)
    # ssh_client.exec_command("systemctl restart zmq-i2c.service")
    # ssh_client.exec_command("systemctl restart zmq-server.service")
    # ssh_client.close()
    # print("hexa-controller servers started")

    daqsocket = zmqctrl.daqController(options.hexaIP,options.daqPort,options.configFile)
    clisocket = zmqctrl.daqController("localhost",options.pullerPort,options.configFile)
    i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort,options.configFile)
    
    i2csocket.initialize()
    daqsocket.initialize()
    clisocket.yamlConfig['client']['serverIP'] = daqsocket.ip
    clisocket.initialize()

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

    marspedestal_run.pedestal_run(i2csocket,daqsocket,clisocket,options.odir,options.dut)
    marspedestal_scan.pedestal_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut)
    marsvrefinv_scan.vrefinv_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut)
    marsvrefnoinv_scan.vrefnoinv_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut)
    marspedestal_run.pedestal_run(i2csocket,daqsocket,clisocket,options.odir,options.dut)
    marsphase_scan.phase_scan(i2csocket,daqsocket,clisocket,options.odir,options.dut)
