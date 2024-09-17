import zmq, datetime,  os, subprocess, sys, yaml, glob, math
from time import sleep

import myinotifier,util
import analysis.level0.injection_run_analysis as analyzer
import zmq_controler as zmqctrl
from nested_dict import nested_dict

A_T = 3.9083e-3
B_T = -5.7750e-7
R0 = 1000
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
    }

def injection_run(i2csocket,daqsocket, clisocket, basedir,device_name, injectionConfig,refinv_nr,errorflag):
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

    #phase=injectionConfig['phase']
    #BXoffset=injectionConfig['BXoffset']
    Bx_phase=injectionConfig['Bx_phase']
    gain = injectionConfig['gain'] # 0 for low range ; 1 for high range
    globalTotThr = injectionConfig['globalTotThr']
    globalToaThr = injectionConfig['globalToaThr']
    calib_dac = injectionConfig['calib_dac'] #
    injectedChannels=injectionConfig['injectedChannels']
    Nevt = injectionConfig['Nevt']
    voltages = injectionConfig['OV']
    LEDvolt = injectionConfig['LEDvolt']
    TB_type = injectionConfig['TB_type']
    testName="injection_run"
    for OV in voltages:
        # Bias Voltage Adjustment
        i2csocket.set_gbtsca_dac("A",OV_dict[TB_type][OV]["A"])
        print("Dac A value is now",i2csocket.read_gbtsca_dac("A"))
        i2csocket.set_gbtsca_dac("B",OV_dict[TB_type][OV]["B"])
        print("Dac B value is now",i2csocket.read_gbtsca_dac("B"))


        print(" ")
        print("Voltage set to OV=",OV,"V")
        # "sleep" is only required when SiPM bias voltage is changed:
        print(" ")
        print(" Please wait for voltage stabilization (5seconds)")
        sleep(2)   # wait 2s for stabilization of voltages before readback


        for BxOff_val in Bx_phase.keys():
            for phase_val in Bx_phase[BxOff_val]:


                i2csocket.configure()

                odir_main = "%s/%s/TB2p1_2_LED_scan_OV%s_extLED%imV/"%( os.path.realpath(basedir), device_name, OV, LEDvolt) # a comlete path is needed
                if not os.path.exists(odir_main):os.makedirs(odir_main)

                fout=open(odir_main+"/TB2_info.txt", "a")
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

                ADC = i2csocket.read_gbtsca_adc(12)
                LED_BIAS = round(float(ADC)/4095*15000/1000, 3)
                print("LED_BIAS = ", str(LED_BIAS))
                fout.write("LED_BIAS: " + str(LED_BIAS) + '\n')

                #odir = "%s/run_BX%i_phase%i"%(odir_main, BxOff_val,phase_val) # a comlete path is needed
                odir = "%s/run_BX%i_phase%i_ref%i"%(odir_main, BxOff_val,phase_val,refinv_nr) # a comlete path is needed
                os.makedirs(odir)

                mylittlenotifier = myinotifier.mylittleInotifier(odir=odir)
                mylittlenotifier.start()

                clisocket.yamlConfig['global']['outputDirectory'] = odir
                clisocket.yamlConfig['global']['run_type'] = "injection_run"
                clisocket.yamlConfig['global']['serverIP'] = daqsocket.ip
                clisocket.configure()


                daqsocket.yamlConfig['daq']['NEvents']=Nevt
                daqsocket.enable_fast_commands(A=1,B=1)
                daqsocket.l1a_generator_settings(name='A',BX=10,length=4,cmdtype='CALIBREQ',prescale=80,followMode='DISABLE')
                daqsocket.l1a_generator_settings(name='B',BX=10+BxOff_val,length=1,cmdtype='L1A',prescale=80,followMode='A')
                daqsocket.configure()

                chip_params={}
                chip_params['Phase']     = phase_val
                chip_params['BXoffset']  = BxOff_val
                chip_params['Calib_dac'] = calib_dac
                chip_params['Inj_gain'] = gain
                chip_params['Tot_vref'] = globalTotThr
                chip_params['Toa_vref'] = globalToaThr
                chip_params['injectedChannels'] = injectedChannels
                util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,runid=0,testName=testName,keepRawData=1,chip_params=chip_params)
                nestedConf = nested_dict()
                for key in i2csocket.yamlConfig.keys():
                    if key.find('roc_s')==0:
                        nestedConf[key]['sc']['ReferenceVoltage']['all']['IntCtest'] = 0
                        nestedConf[key]['sc']['ReferenceVoltage']['all']['Calib_dac'] = calib_dac
                        nestedConf[key]['sc']['ReferenceVoltage']['all']['Tot_vref'] = globalTotThr
                        nestedConf[key]['sc']['ReferenceVoltage']['all']['Toa_vref'] = globalToaThr
                        nestedConf[key]['sc']['Top']['all']['Phase']=phase_val
                        for injectedChannel in injectedChannels:
                            if injectedChannel in i2csocket.yamlConfig[key]['sc']['ch'].keys():
                                if gain==0:
                                    nestedConf[key]['sc']['ch'][injectedChannel]['LowRange'] = 0
                                    nestedConf[key]['sc']['ch'][injectedChannel]['HighRange'] = 0
                                else:
                                    nestedConf[key]['sc']['ch'][injectedChannel]['LowRange'] = 0
                                    nestedConf[key]['sc']['ch'][injectedChannel]['HighRange'] = 0
                            else:
                               if gain==0:
                                    nestedConf[key]['sc']['ch'][injectedChannel] = {
                                        'LowRange' : 0,
                                        'HighRange' : 0
                                    }
                               else:
                                    nestedConf[key]['sc']['ch'][injectedChannel] = {
                                        'LowRange' : 0 ,
                                        'HighRange' : 0
                                    }
                i2csocket.set_gbtsca_gpio_vals(0x00000080,0x00000080) # LED ON First argument: GPIO value, 2nd argument: Mask
                i2csocket.configure(yamlNode=nestedConf.to_dict())
                i2csocket.resettdc()

                util.saveFullConfig(odir=odir,i2c=i2csocket,daq=daqsocket,cli=clisocket)

                util.acquire(daq=daqsocket, client=clisocket)
                mylittlenotifier.stop()

                run_analyzer = analyzer.injection_run_analyzer(odir=odir)
                files = glob.glob(odir+"/*.root")
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
    refinv = glob.glob(options.configFile+"/*.yaml")
    print(refinv)

    for refinv_val in refinv:
        errorflag = 0

        print(refinv_val)
        daqsocket = zmqctrl.daqController(options.hexaIP,options.daqPort,refinv_val)
        clisocket = zmqctrl.daqController("localhost",options.pullerPort,refinv_val)
        i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort,refinv_val)

        i2csocket.initialize()

    	# Original code #
        injectionConfig = {
            'TB_type' : "TB2.1_3",
            # 'phase' : [0, 2, 4, 6, 8, 10, 12, 14, 16],
            #'phase' : [i for i in range(0,10)],
            # 'phase' : [i for i in range(3,5)],
            #'BXoffset' : [i for i in range(21,22)],
            #'BXoffset' : [i for i in range(22,24)],   # Mini TB: 19(20)-25, TB2.1: 21-27
            #'Bx_phase' : {22:[i for i in range(10,16)],23:[j for j in range(0,3)]}, ## TB2.1_2
            #'Bx_phase' : {22:[i for i in range(8,15)]}, ## TB2.1_3
            # 'Bx_phase' : {22:[i for i in range(8,15)],23:[j for j in range(0,5)]}, ## TB2.1_3
            'Bx_phase' : {22:[10]}, ## TB2.1_3
            'gain' : 1,
            'globalTotThr' : 350,
            'globalToaThr' : 300,
            'calib_dac' : 0,
            'injectedChannels' : [47,45,48,46,57,55,58,56,51,49,52,50,61,59,62,60],
            'Nevt' : '1000',
            'LEDvolt' : 6100,
            #'OV'    : ['6V','4V']
            'OV'    : ['6V']
            }

    	# edited by Malinda 20-Sept-2021
    	#injectionConfig = {
    	#	'phase' : 13,
    	#	'BXoffset' : 19,
    	#	'gain' : 1,
    	#	'globalTotThr' : 150,
    	#	'globalToaThr' : 100,
    	#	'calib_dac' : 100,
    	#	'injectedChannels' : [10,30,49,69]
    	#}
        refinv_nr = refinv_val[refinv_val.find("_refinv")+7:refinv_val.find("_refinv")+8]
        print(refinv_nr)

        injection_run(i2csocket,daqsocket,clisocket,options.odir,options.dut,injectionConfig,int(refinv_nr),errorflag)
