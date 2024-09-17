import zmq, datetime,  os, subprocess, sys, yaml, glob

import myinotifier,util,math,time
import zmq_controler as zmqctrl
from nested_dict import nested_dict

A_T = 3.9083e-3
B_T = -5.7750e-7
R0 = 1000

OV = ["2V","4V"]
TB_type = "TB2.1_3"

OV_dict = {
    "TB2": {
        '2V': {'A':180,'B':125},
        '3V': {'A':185,'B':125},
        '3V5': {'A':187,'B':125},
        '4V': {'A':190,'B':125},
        '4V5': {'A':193,'B':125},
        '5V': {'A':195,'B':125},
        '5V5': {'A':195,'B':125},
        '6V': {'A':200,'B':125}},
     "TB2.1_2": {
        '2V': {'A':193,'B':120},
        '3V': {'A':198,'B':122},
        '3V5': {'A':201,'B':125},
        '4V': {'A':203,'B':122},
        '4V5': {'A':206,'B':125},
        '5V': {'A':209,'B':120},
        '5V5': {'A':211,'B':125},
        '6V': {'A':213,'B':122}},
     "TB2.1_3": {
        '2V': {'A':195,'B':122},
        '3V': {'A':200,'B':124},
        '3V5': {'A':203,'B':125},
        '4V': {'A':205,'B':126},
        '4V5': {'A':208,'B':127},
        '5V': {'A':210,'B':128},
        '5V5': {'A':213,'B':129},
        '6V': {'A':215,'B':130}}

     "TB3_1": {
        '2V': {'A':195,'B':122},
        '3V': {'A':200,'B':124},
        '3V5': {'A':203,'B':125},
        '4V': {'A':205,'B':126},
        '4V5': {'A':208,'B':127},
        '5V': {'A':210,'B':128},
        '5V5': {'A':213,'B':129},
        '6V': {'A':215,'B':130}}
     "TB3_2": {
        '2V': {'A':195,'B':122},
        '3V': {'A':200,'B':124},
        '3V5': {'A':203,'B':125},
        '4V': {'A':205,'B':126},
        '4V5': {'A':208,'B':127},
        '5V': {'A':210,'B':128},
        '5V5': {'A':213,'B':129},
        '6V': {'A':215,'B':130}}

    }


def beamtestrun(i2csocket,daqsocket, clisocket, basedir,device_name,nruns,nevents,voltage,errorflag):

    if type(i2csocket) != zmqctrl.i2cController:
        print( "ERROR in beamtestrun : i2csocket should be of type %s instead of %s"%(zmqctrl.i2cController,type(i2csocket)) )
        sleep(1)
        return
    if type(daqsocket) != zmqctrl.daqController:
        print( "ERROR in beamtestrun : daqsocket should be of type %s instead of %s"%(zmqctrl.daqController,type(daqsocket)) )
        sleep(1)
        return

    if type(clisocket) != zmqctrl.daqController:
        print( "ERROR in beamtestrun : clisocket should be of type %s instead of %s"%(zmqctrl.daqController,type(clisocket)) )
        sleep(1)
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    testName = "beamtestrun"
    odir = "%s/%s/beamtestrun/run_OV%s_%s/"%( os.path.realpath(basedir), device_name, voltage, timestamp )
    os.makedirs(odir)

    fout=open(odir+"TB2_info.txt", "x")
    fout.write("####  Before data capture ####" + '\n')
    fout.write("#  Tileboard2 Slow Control Data" + '\n')
    fout.write("#  Date, Time: " + timestamp + '\n')


    SCA_ADC_range = range(0, 8)
    for sca_adc in SCA_ADC_range:
       ADC = i2csocket.read_gbtsca_adc(sca_adc)
       T1 = round(float((-R0*A_T + math.sqrt(math.pow(R0*A_T, 2) - 4*R0*B_T*(R0-(1800 / ((2.5*4095/float(ADC))-1))))) / (2*R0*B_T)),1)
       print("T", sca_adc,  ":", str(T1))
       fout.write("T" + str(sca_adc) +": "+str(T1) + '\n')

    ADC = i2csocket.read_gbtsca_adc(9)
    MPPC_BIAS1 = round(float(ADC)/4095*204000/4000, 4)
    print("MPPC_BIAS1 = ", str(MPPC_BIAS1))
    fout.write("MPPC_BIAS1: " + str(MPPC_BIAS1) + '\n')

    ADC = i2csocket.read_gbtsca_adc(10)
    MPPC_BIAS2 = round(float(ADC)/4095*204000/4000, 4)
    print("MPPC_BIAS2 = ", str(MPPC_BIAS2))
    fout.write("MPPC_BIAS2: " + str(MPPC_BIAS2) + '\n')


    mylittlenotifier = myinotifier.mylittleInotifier(odir=odir)
    mylittlenotifier.start()

    clisocket.yamlConfig['global']['outputDirectory'] = odir
    clisocket.yamlConfig['global']['run_type'] = testName
    clisocket.yamlConfig['global']['serverIP'] = daqsocket.ip
    clisocket.configure()
    daqsocket.yamlConfig['daq']['NEvents']=nevents
    daqsocket.yamlConfig['daq']['Number_of_events_per_readout'] = '10'
    daqsocket.enable_fast_commands(external=1)
    # daqsocket.l1a_settings(bx_spacing=45,length=43*6,external_debounced=1)
    # daqsocket.l1a_settings(bx_spacing=45,length=6,external_debounced=1)
    daqsocket.l1a_settings(bx_spacing=45,length=6,external_debounced=1)
    daqsocket.configure()


    # nestedConf = nested_dict()
    # for key in i2csocket.yamlConfig.keys():
    #     if key.find('roc_s')==0:
    #         for ch in range(0,36):
    #             nestedConf[key]['sc']['ch'][ch]['Channel_off']=1
    #         nestedConf[key]['sc']['calib'][0]['Channel_off']=1
    # i2csocket.update_yamlConfig(yamlNode=nestedConf.to_dict())
    # i2csocket.configure()

    util.saveFullConfig(odir=odir,i2c=i2csocket,daq=daqsocket,cli=clisocket)
    clisocket.start()
    for run in range(nruns):
        util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,runid=run,testName=testName,keepRawData=1,chip_params={})
        util.acquire_scan(daq=daqsocket)

    clisocket.stop()
    try:
        mylittlenotifier.stop()
    except :
        print("REDOOOO THIS MEASUREMENT!!!!!!")
        errorflag=1

    fout.write("####  After data capture ####" + '\n')
    fout.write("#  Tileboard2 Slow Control Data" + '\n')
    fout.write("#  Date, Time: " + timestamp + '\n')

    SCA_ADC_range = range(0, 8)
    for sca_adc in SCA_ADC_range:
       ADC = i2csocket.read_gbtsca_adc(sca_adc)
       T1 = round(float((-R0*A_T + math.sqrt(math.pow(R0*A_T, 2) - 4*R0*B_T*(R0-(1800 / ((2.5*4095/float(ADC))-1))))) / (2*R0*B_T)),1)
       print("T", sca_adc,  ":", str(T1))
       fout.write("T" + str(sca_adc) +": "+str(T1) + '\n')

    ADC = i2csocket.read_gbtsca_adc(9)
    MPPC_BIAS1 = round(float(ADC)/4095*204000/4000, 4)
    print("MPPC_BIAS1 = ", str(MPPC_BIAS1))
    fout.write("MPPC_BIAS1: " + str(MPPC_BIAS1) + '\n')

    ADC = i2csocket.read_gbtsca_adc(10)
    MPPC_BIAS2 = round(float(ADC)/4095*204000/4000, 4)
    print("MPPC_BIAS2 = ", str(MPPC_BIAS2))
    fout.write("MPPC_BIAS2: " + str(MPPC_BIAS2) + '\n')

    return odir


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option("-d", "--dut", dest="dut",
                      help="device under test")

    parser.add_option("-i", "--hexaIP",
                      action="store", dest="hexaIP",
                      help="IP address of the zynq on the hexactrl board")

    parser.add_option("-f", "--configFile",default="./data/current_config/initial_full_config.yaml",
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

    parser.add_option("-r","--nruns",
                      action="store", dest="nruns",default=1,type=int,
                      help="number of consecutive runs")

    parser.add_option("-N","--nevents",
                      action="store", dest="nevents",default="1000",
                      help="number of events per run")


    (options, args) = parser.parse_args()
    print(options)


    for voltages in OV:

        daqsocket = zmqctrl.daqController(options.hexaIP,options.daqPort,options.configFile)
        clisocket = zmqctrl.daqController("localhost",options.pullerPort,options.configFile)
        i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort,options.configFile)

    #with open("data/beam/runid") as f:
    #    runid = int(f.readline())+1
    #odir = "%s/%d" % (options.odir,runid )
    #with open("data/beam/runid","w") as f:
    #    f.write(str(runid))


        i2csocket.set_gbtsca_dac("A",OV_dict[TB_type][voltages]["A"])
        print("Dac A value is now",i2csocket.read_gbtsca_dac("A"))
        i2csocket.set_gbtsca_dac("B",OV_dict[TB_type][voltages]["B"])
        print("Dac B value is now",i2csocket.read_gbtsca_dac("B"))

        """
        print(" ################ ")
        print(" PLEASE adjust and run 'python3 TB2_SlowControl.py -i 10.254.56.33 -d TB2' before to configure BV, LED system and GBT_SCA GPIOs ")
        print(" ################ ")
        """
        print(" ")
        print("Voltage set to OV=",voltages,"V")

        # "sleep" is only required when SiPM bias voltage is changed:
        print(" ")
        print(" Please wait for voltage stabilization (5seconds)")
        time.sleep(5)   # wait 5s for stabilization of voltages before readback

        i2csocket.configure()
        # l1aoffset=[0]
        l1aoffset=[11]
        # l1aoffset=[11]
        # l1aoffset=[9]

        errorflag = 0
        for offset in l1aoffset:
            print(offset)
            nestedConf = nested_dict()
            for key in i2csocket.yamlConfig.keys():
                if key.find('roc_s')==0:
                    nestedConf[key]['sc']['DigitalHalf']['all']['L1Offset'] = offset
            i2csocket.configure(yamlNode=nestedConf.to_dict())
            i2csocket.update_yamlConfig(yamlNode=nestedConf.to_dict()) #next step keeps the knowledge of what was changed


        # overwrite settings from script call
        my_calib_dac = 0
        nestedConf = nested_dict()
        [nestedConf[key]['sc']['ReferenceVoltage']['all'].update({'IntCtest':0}) for key in i2csocket.yamlConfig.keys() if key.find('roc_s')==0 ]
        [nestedConf[key]['sc']['ReferenceVoltage']['all'].update({'ExtCtest':0}) for key in i2csocket.yamlConfig.keys() if key.find('roc_s')==0 ]
        [nestedConf[key]['sc']['ReferenceVoltage']['all'].update({'Calib_dac':my_calib_dac}) for key in i2csocket.yamlConfig.keys() if key.find('roc_s')==0 ]

        i2csocket.configure(yamlNode=nestedConf.to_dict())

        beamtestrun(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.nruns,options.nevents,voltages,errorflag)

        if errorflag >0: break
