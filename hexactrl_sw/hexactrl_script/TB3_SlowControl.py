import zmq, datetime,  os, subprocess, sys, yaml, glob

import myinotifier,util,math, datetime
import analysis.level0.pedestal_run_analysis as analyzer
import zmq_controler as zmqctrl
from nested_dict import nested_dict
import time
'''
OV_dict = {
    "TB2": {
        '2V': {'A':180,'B':125},
        '3V': {'A':185,'B':125},
        '3V5': {'A':187,'B':125},
        '4V': {'A':190,'B':125},
        '4V5': {'A':193,'B':125},
        '5V': {'A':195,'B':125},
        '5V5': {'A':195,'B':125},
        '6V': {'A':200,'B':125},
     },
     "TB2.1_2": {
        '2V': {'A':193,'B':120},
        '3V': {'A':198,'B':122},
        '3V5': {'A':201,'B':125},
        '4V': {'A':203,'B':122},
        '4V5': {'A':206,'B':125},
        '5V': {'A':209,'B':120},
        '5V5': {'A':211,'B':125},
        '6V': {'A':213,'B':122},
     },
     "TB2.1_3": {
        '1V': {'A':192,'B':121},
        '1V4': {'A':192,'B':121},
        '1V6': {'A':193,'B':121},
        '1V8': {'A':194,'B':122},
        '2V': {'A':195,'B':122},
        '2V2': {'A':196,'B':124},
        '3V': {'A':200,'B':124},
        '3V5': {'A':203,'B':125},
        '4V': {'A':205,'B':126},
        '4V5': {'A':208,'B':127},
        '5V': {'A':210,'B':128},
        '5V5': {'A':213,'B':129},
        '6V': {'A':215,'B':130},
     },
     "TB3_D8_1": {
        '0V9': {'A':188,'B':136},  # 40.5
        '1V': {'A':189,'B':134},  # 40.6
        '1V1': {'A':190,'B':132}, # 40.7
        '1V2': {'A':191,'B':130}, # 40.8
        '1V3': {'A':192,'B':128}, # 40.9
        '1V4': {'A':193,'B':126}, # 41.0
        '1V9': {'A':196,'B':122},#correct, MPPC_BIAS1 = 41.5099
        '2V': {'A':197,'B':120},#correct, MPPC_BIAS1 = 41.6095
        '2V1': {'A':198,'B':118},#correct, MPPC_BIAS1 = 41.7092
        '2V2': {'A':199,'B':116},#correct, MPPC_BIAS1 = 41.8337
        '2V3': {'A':200,'B':114},#correct, MPPC_BIAS1 = 41.9209
        '2V4': {'A':201,'B':111},#correct, MPPC_BIAS1 = 41.9956
        '2V5': {'A':202,'B':107},#correct, MPPC_BIAS1 = 42.0205
        '2V6': {'A':203,'B':107},# correct, MPPC_BIAS1 = 42.1949
        '4V': {'A':210,'B':118}, # 43.9 V, Aug 2023 test beam, MPPC_BIAS1 = 43.9 V ----------------Aug2023
        '6V':  {'A': 219, 'B': 126},  # 45.9 V  MPPC_BIAS1 =  45.9934, not corrected
     },
        
     "TB3_D8_2": {
        '2V': {'C':183,'D':122},
        '4V': {'C':193,'D':122},
     },
        
     "miniTB": {
        '4V':  {'A': 1000, 'B': 1000},  # 43.6 V
        '5V':  {'A': 1000, 'B': 1000},  # 44.6 V
        '6V':  {'A': 1000, 'B': 1000},  # 45.6 V
        '6V6': {'A': 1000, 'B': 1000},  # 46.2 V
     },
     "TB3_G8_1": {
        #'1V':  {'A': 180, 'B': 127},  # 40.9 V  MPPC_BIAS1 =  40.8996
        '2V':  {'A': 183, 'B': 124},  # 41.9 V  MPPC_BIAS1 =  41.88
        '4V':  {'A': 193, 'B': 124},  # 43.9 V  MPPC_BIAS1 =  43.9136
        #'5V':  {'A': 202, 'B': 126},  # 44.9 V  MPPC_BIAS1 =  44.9348
        '6V':  {'A': 207, 'B': 110},  # 45.9 V  MPPC_BIAS1 =  46.6659
        #'6V6':  {'A': 210, 'B': 126},  # 46.5 V MPPC_BIAS1 =  46.4916
     },
     
     "TB3_G8_2": {
        #'1V':  {'A': 180, 'B': 127},  # 40.9 V  MPPC_BIAS1 =  40.8996
        '2V':  {'A': 186, 'B': 126},  # 41.9 V  MPPC_BIAS1 =  41.896 ----------------Aug2023
        '4V':  {'A': 197, 'B': 124},  # 43.9 V  MPPC_BIAS1 =  43.9385  --------------Aug2023
        #'5V':  {'A': 202, 'B': 126},  # 44.9 V  MPPC_BIAS1 =  44.9348
        '6V':  {'A': 210, 'B': 112},  # 45.9 V  MPPC_BIAS1 =  45.956 ----------------Aug2023
        #'6V6':  {'A': 210, 'B': 126},  # 46.5 V MPPC_BIAS1 =  46.4916
     },
     
     "TB3_A5_1": {
        #'1V':  {'A': 180, 'B': 127},  # 40.9 V  MPPC_BIAS1 =  40.8996
        '2V':  {'A': 190, 'B': 122},  # 41.9 V  MPPC_BIAS1 =  43.9385  --------------Aug2023
        '4V':  {'A': 200, 'B': 124},  # 43.9 V  MPPC_BIAS1 =  41.896 ----------------Aug2023
        #'5V':  {'A': 202, 'B': 126},  # 44.9 V  MPPC_BIAS1 =  44.9348
        '6V':  {'A': 211, 'B': 122},  # 45.9 V  MPPC_BIAS1 =  45.956 ----------------Aug2023
        #'6V6':  {'A': 210, 'B': 126},  # 46.5 V MPPC_BIAS1 =  46.4916
     },
     "TB3_D8_7": {
        #'4V':  {'A': 185, 'B': 127},  # 43.9 V  MPPC_BIAS1 =  43.6645, for room temperature
        #'4V':  {'A': 170, 'B': 126},  # 41.9668 V  T 7 : -28.7, MPPC_BIAS1 =  41.9582
        '4V':  {'A': 185, 'B': 129},  # 43.882 V  T 7 : 24.4, MPPC_BIAS1 =  43.8637
     },
     "TB3_D8_9": {
        #'4V':  {'A': 181, 'B': 130},  # 43.9 V  MPPC_BIAS1 =  43.7392, for room temperature
        #'4V':  {'A': 170, 'B': 135},  # 42.352 V,  T 7 : -18.5, MPPC_BIAS1 =  42.3568
        '4V':  {'A': 181, 'B': 133},  # 44.085 V,  T 7 : 30.5, MPPC_BIAS1 =  44.0879
     },
     "TB3_D8_10": {
        #'4V':  {'A': 200, 'B': 125},  # 43.9 V  for room temperature
        #'4V':  {'A': 200, 'B': 132},  # 43.9 V,  T 7 : -33.1, MPPC_BIAS1 =  41.8088
        '4V':  {'A': 200, 'B': 131},  # 44.1556 V  T 7 : 32.1, MPPC_BIAS1 =  44.1253
     },  
'''
     
OV_dict = {
     #MAY testbeam
     "TB3_G8_6": {
        '4V': {'A': 197, 'B': 125}, #43.78V
     },
     "TB3_G8_4": {
        '4V': {'A': 187, 'B': 128}, #43.82V
     },
     
     "TB3_E8_2": {
        '4V': {'A': 188, 'B': 125}, #43.96V
     },
     "TB3_E8_3": {
        '4V': {'A': 200, 'B': 128}, #43.76V
     },
     "TB3_E8_4": {
        '4V': {'A': 196, 'B': 130}, #43.72V
     },
     "TB3_E8_5": {
        '4V': {'A': 180, 'B': 125}, #43.92V
     },
     "TB3_E8_6": { 
        '4V': {'A': 187, 'B': 122}, #43.89V
     },
     "TB3_A5_1": { 
        '4V': {'A': 200, 'B': 125}, #43.8V
     }, 
     "TB3_A5_2": { 
        '4V': {'A': 178, 'B': 120}, #43.97V
     }, 
     "TB3_A5_5": { 
        '4V': {'A': 181, 'B': 128}, #43.83V
     }, 
     "TB3_A5_6": { 
        '4V': {'A': 188, 'B': 125}, #43.83V
     },
     
     
     "TB3_D8_4": { 
        '4V': {'A': 182, 'B': 125}, #43.86V
     },
     
     "TB3_D8_10": { 
        '4V': {'A': 200, 'B': 125}, #43.79V
     },

     "TB3_D8_3": { 
        '4V': {'A': 186, 'B': 136}, #43.88V
     },
     
     "TB3_D8_5": { 
        '4V': {'A': 195, 'B': 126}, #43.91V
     },
     
     "TB3_D8_6": { 
        '4V': {'A': 195, 'B': 124}, #43.93V
     },
     
     "TB3_D8_8": { 
        '4V': {'A': 195, 'B': 125}, #43.81V
     },
     
     "TB3_D8_11": {
        '4V': {'A': 194, 'B': 122}, #43.89V
     },
     "TB3_D8_12": {
        '4V': {'A': 187, 'B': 120}, #43.97V
     },
     
     "TB3_B12_1": {
        '4V': {'A': 187, 'B': 120}, #43.97V
     },
     
     "TB3_B12_2": {
        '4V': {'A': 187, 'B': 120}, #43.97V
     },
     
}



def read_sca_config(i2csocket,daqsocket, clisocket, basedir,tileboard,OV):
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
    testName = "TB2_SlowControl"
    odir = "%s/%s/slow_control/run_%s/"%( os.path.realpath(basedir), tileboard, timestamp )
    os.makedirs(odir)

    mylittlenotifier = myinotifier.mylittleInotifier(odir=odir)
    mylittlenotifier.start()

    #======================================change for v3 tile board test==============
    #daqsocket.yamlConfig['daq']['NEvents']='0'   # was 10000
    #daqsocket.enable_fast_commands(random=1)
    #daqsocket.l1a_settings(bx_spacing=45)
    #daqsocket.configure()
 
    clisocket.yamlConfig['client']['outputDirectory'] = odir
    clisocket.yamlConfig['client']['run_type'] = testName
    clisocket.configure()
    daqsocket.yamlConfig['daq']['active_menu']='randomL1A'
    daqsocket.yamlConfig['daq']['menus']['randomL1A']['NEvents']=0 #10000
    daqsocket.yamlConfig['daq']['menus']['randomL1A']['log2_rand_bx_period']=0
    daqsocket.yamlConfig['daq']['menus']['randomL1A']['bx_min']=45

    daqsocket.configure()
    
    nestedConf = nested_dict()

    print(" ")
    print(" ")
    print(" Slow-Control from GBT_SCA ")
    print(" ")

    outdir = odir
    path=outdir
    fout=open(outdir+"TB2_info.txt", "x")
    fout.write("#  Tileboard2 Slow Control Data" + '\n')
    fout.write("#  Date, Time: " + timestamp + '\n')


    ##### Set GPIOs  ################
    
    print("OV:",OV)
    '''
    print("Set GPIOs")
    i2csocket.set_gbtsca_gpio_direction(0x0fffff9C) # '0': input, '1': output

    # enable MPPC_BIAS1 ("1"), disable MPPC_BIAS2 ("0"): GPIOs 20, 21
    i2csocket.set_gbtsca_gpio_vals(0x00200000,0x00300000) # First argument: GPIO value, 2nd argument: Mask #TB 2
    
    if tileboard=="TB3_2":
    	i2csocket.set_gbtsca_gpio_vals(0x00200000,0x00300000) # First argument: GPIO value, 2nd argument: Mask #TB 2
    else:
    	i2csocket.set_gbtsca_gpio_vals(0x00100000,0x00300000) # First argument: GPIO value, 2nd argument: Mask #TB 1
    

    # global enable LED system: LED_ON_OFF ('1': LED system ON), GPIO7:
    #i2csocket.set_gbtsca_gpio_vals(0x00000000,0x00000080) # LED OFF First argument: GPIO value, 2nd argument: Mask
    i2csocket.set_gbtsca_gpio_vals(0x00000080,0x00000080) # LED ON First argument: GPIO value, 2nd argument: Mask

    # put LED_DISABLE1 and LED_DISABLE2 to '0' ('0': LED system ON), GPIOs 8-15
    #i2csocket.set_gbtsca_gpio_vals(0x00000000,0x0000ff00) # First argument: GPIO value, 2nd argument: Mask
    i2csocket.set_gbtsca_gpio_vals(0x00000000,0x0000ff00) # First argument: GPIO value, 2nd argument: Mask

    print("GPIO values are",hex(int(i2csocket.read_gbtsca_gpio())))   # should give 0x1000Cf in normal operation with MPPC_BIAS1 ON
    print("GPIO directions are",hex(int(i2csocket.get_gbtsca_gpio_direction())))
    '''

    ##### Set GBT_SCA DACs for MPPC Bias Voltage (Reference)  ################

    '''
    first column: DAC0 ('DAC A') setting
    2nd column: DAC1 ('DAC B') setting
    3rd column: MPPC_BIAS1, measured at ALDOv2 output with multimeter

    BV_IN = 46.5V (Tileboard BV input)

    Caution: Do not apply higher voltages than 6V overvoltage
    Caution: Do never supply BV_IN > 50V to the Tileboard


    '''
    print("Set DACs")
    ######################
    # Set DACs of GBT_SCA TB2
    # Bias Voltage = 41.5V (OV = 2.0V)
    
    if tileboard=="TB3_2":
        i2csocket.set_gbtsca_dac("A",100)
        print("Dac A value is now",i2csocket.read_gbtsca_dac("A"))
        i2csocket.set_gbtsca_dac("B",100)
        print("Dac B value is now",i2csocket.read_gbtsca_dac("B"))
        '''
        i2csocket.set_gbtsca_dac("A",200)
        print("Dac A value is now",i2csocket.read_gbtsca_dac("A"))
        i2csocket.set_gbtsca_dac("B",125)
        print("Dac B value is now",i2csocket.read_gbtsca_dac("B"))
        '''
        i2csocket.set_gbtsca_dac("C",OV_dict[tileboard][OV]['C'])
        print("Dac C value is now",i2csocket.read_gbtsca_dac("C"))
        i2csocket.set_gbtsca_dac("D",OV_dict[tileboard][OV]['D'])
        print("Dac D value is now",i2csocket.read_gbtsca_dac("D"))

    
    else:
        i2csocket.set_gbtsca_dac("A",OV_dict[tileboard][OV]['A'])
        print("Dac A value is now",i2csocket.read_gbtsca_dac("A"))
        i2csocket.set_gbtsca_dac("B",OV_dict[tileboard][OV]['B'])
        print("Dac B value is now",i2csocket.read_gbtsca_dac("B"))
        '''
        i2csocket.set_gbtsca_dac("A",200)
        print("Dac A value is now",i2csocket.read_gbtsca_dac("A"))
        i2csocket.set_gbtsca_dac("B",125)
        print("Dac B value is now",i2csocket.read_gbtsca_dac("B"))
        '''
        i2csocket.set_gbtsca_dac("C",100)
        print("Dac C value is now",i2csocket.read_gbtsca_dac("C"))
        i2csocket.set_gbtsca_dac("D",100)
        print("Dac D value is now",i2csocket.read_gbtsca_dac("D"))


    # "sleep" is only required when SiPM bias voltage is changed:
    print(" ")
    print(" Please wait for voltage stabilization (5seconds)")
    time.sleep(5)   # wait 5s for stabilization of voltages before readback


    ########################   ADCs   ####################

    print(" ")
    print(" ADCs: ")

    A_T = 3.9083e-3
    B_T = -5.7750e-7
    R0 = 1000
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

    ADC = i2csocket.read_gbtsca_adc(11)
    VCC_IN = round(float(ADC)/4095*15000/1000, 3)
    print("VCC_IN = ", str(VCC_IN))
    fout.write("VCC_IN: " + str(VCC_IN) + '\n')

    ADC = i2csocket.read_gbtsca_adc(12)
    LED_BIAS = round(float(ADC)/4095*15000/1000, 3)
    print("LED_BIAS = ", str(LED_BIAS))
    fout.write("LED_BIAS: " + str(LED_BIAS) + '\n')

    ADC = i2csocket.read_gbtsca_adc(13)
    VPA = round(float(ADC)/4095*4000/1000, 3)
    print("VPA (+2.5V) = ", str(VPA))
    fout.write("VPA: " + str(VPA) + '\n')

    ADC = i2csocket.read_gbtsca_adc(14)
    # print(str(ADC))
    PRE_VPA = round(float(ADC)/4095*4000/1000, 3)
    print("PRE_VPA (around +3.5V) = ", str(PRE_VPA))
    fout.write("PRE_VPA: " + str(PRE_VPA) + '\n')

    ADC = i2csocket.read_gbtsca_adc(15)
    VDDA = round(float(ADC)/4095*2000/1000, 3)
    print("VDDA (+1.2V) = ", str(VDDA))
    fout.write("VDDA: " + str(VDDA) + '\n')

    ADC = i2csocket.read_gbtsca_adc(16)
    VDDD = round(float(ADC)/4095*2000/1000, 3)
    print("VDDD (+1.2V) = ", str(VDDD))
    fout.write("VDDD: " + str(VDDD) + '\n')

    ADC = i2csocket.read_gbtsca_adc(17)
    PRE_VDDA = round(float(ADC)/4095*2000/1000, 3)
    print("PRE_VDDA (+1.5V) = ", str(PRE_VDDA))
    fout.write("PRE_VDDA: " + str(PRE_VDDA) + '\n')

    ADC = i2csocket.read_gbtsca_adc(27)
    TB_ID0 = round(float(ADC)/4095, 2)
    print("TB_ID0 (+0.2V) = ", str(TB_ID0))
    fout.write("TB_ID0: " + str(TB_ID0) + '\n')

    ADC = i2csocket.read_gbtsca_adc(28)
    TB_ID1 = round(float(ADC)/4095, 2)
    print("TB_ID1 (+0.0V) = ", str(TB_ID1))
    fout.write("TB_ID1: " + str(TB_ID1) + '\n')

    ADC = i2csocket.read_gbtsca_adc(29)
    TB_ID2 = round(float(ADC)/4095, 2)
    print("TB_ID2 (+0.0V) = ", str(TB_ID2))
    fout.write("TB_ID2: " + str(TB_ID2) + '\n')


    ########################   GPIOs    ####################
    '''
    print(" ")
    print(" GPIOs")

    SCA_IOS = int(i2csocket.read_gbtsca_gpio())

    print("ERROR (no error = 1): ", hex(SCA_IOS & 0x00000001))
    fout.write("ERROR: " + str(hex(SCA_IOS & 0x00000001)) + '\n')

    print("PLL_LCK (no error = 1): ", hex((SCA_IOS & 0x00000002)>>1))
    fout.write("PLL_LCK: " + str(hex((SCA_IOS & 0x00000002)>>1)) + '\n')

    print("RSTB (no reset = 1): ", hex((SCA_IOS & 0x00000004)>>2))
    fout.write("RSTB: " + str(hex((SCA_IOS & 0x00000004)>>2)) + '\n')

    print("I2C_RSTB (no reset = 1): ", hex((SCA_IOS & 0x00000008)>>3))
    fout.write("I2C_RSTB: " + str(hex((SCA_IOS & 0x00000008)>>3)) + '\n')

    print("RESYNCLOAD (usually at 0): ", hex((SCA_IOS & 0x00000010)>>4))
    fout.write("RESYNCLOAD: " + str(hex((SCA_IOS & 0x00000010)>>4)) + '\n')

    print("SEL_CK_EXT (not used in ROCv3): ", hex((SCA_IOS & 0x00000040)>>6))
    fout.write("SEL_CK_EXT: " + str(hex((SCA_IOS & 0x00000040)>>6)) + '\n')

    print("LED_ON_OFF (1: ON): ", hex((SCA_IOS & 0x00000080)>>7))
    fout.write("LED_ON_OFF: " + str(hex((SCA_IOS & 0x00000080)>>7)) + '\n')

    print("LED_DISABLE1 (1: OFF): ", hex((SCA_IOS & 0x00000100)>>8))
    fout.write("LED_DISABLE1: " + str(hex((SCA_IOS & 0x00000100)>>8)) + '\n')

    print("LED_DISABLE2 (1: OFF): ", hex((SCA_IOS & 0x00000200)>>9))
    fout.write("LED_DISABLE2: " + str(hex((SCA_IOS & 0x00000200)>>9)) + '\n')

    print("LED_DISABLE3 (1: OFF): ", hex((SCA_IOS & 0x00000400)>>10))
    fout.write("LED_DISABLE3: " + str(hex((SCA_IOS & 0x00000400)>>10)) + '\n')

    print("LED_DISABLE4 (1: OFF): ", hex((SCA_IOS & 0x00000800)>>11))
    fout.write("LED_DISABLE4: " + str(hex((SCA_IOS & 0x00000800)>>11)) + '\n')

    print("LED_DISABLE5 (1: OFF): ", hex((SCA_IOS & 0x00001000)>>12))
    fout.write("LED_DISABLE5: " + str(hex((SCA_IOS & 0x00001000)>>12)) + '\n')

    print("LED_DISABLE6 (1: OFF): ", hex((SCA_IOS & 0x00002000)>>13))
    fout.write("LED_DISABLE6: " + str(hex((SCA_IOS & 0x00002000)>>13)) + '\n')

    print("LED_DISABLE7 (1: OFF): ", hex((SCA_IOS & 0x00004000)>>14))
    fout.write("LED_DISABLE7: " + str(hex((SCA_IOS & 0x00004000)>>14)) + '\n')

    print("LED_DISABLE8 (1: OFF): ", hex((SCA_IOS & 0x00008000)>>15))
    fout.write("LED_DISABLE8: " + str(hex((SCA_IOS & 0x00008000)>>15)) + '\n')

    print("EN_HV0 (ALDOV2 BV1 (1: ON): ", hex((SCA_IOS & 0x00100000)>>20))
    fout.write("EN_HV0: " + str(hex((SCA_IOS & 0x00100000)>>20)) + '\n')

    print("EN_HV1 (ALDOV2 BV2 (1: ON): ", hex((SCA_IOS & 0x00200000)>>21))
    fout.write("EN_HV1: " + str(hex((SCA_IOS & 0x00200000)>>21)) + '\n')
    '''
    ########################   DACs   ####################

    print(" ")
    print(" DACs:")

    print("SCA DAC A (BV1 coarse) value: ",i2csocket.read_gbtsca_dac("A"))
    fout.write("DAC_A: " + i2csocket.read_gbtsca_dac("A") + '\n')

    print("SCA DAC B (BV1 fine) value: ",i2csocket.read_gbtsca_dac("B"))
    fout.write("DAC_B: " + i2csocket.read_gbtsca_dac("B") + '\n')

    print("SCA DAC C (BV2 coarse) value: ",i2csocket.read_gbtsca_dac("C"))
    fout.write("DAC_C: " + i2csocket.read_gbtsca_dac("C") + '\n')

    print("SCA DAC D (BV2 fine) value: ",i2csocket.read_gbtsca_dac("D"))
    fout.write("DAC_D: " + i2csocket.read_gbtsca_dac("D") + '\n')


    fout.close()

    i2csocket.configure(yamlNode=nestedConf.to_dict())


    # nestedConf = nested_dict()
    # for key in i2csocket.yamlConfig.keys():
    #     if key.find('roc_s')==0:
    #         for ch in range(0,36):
    #             nestedConf[key]['sc']['ch'][ch]['Channel_off']=1
    #         nestedConf[key]['sc']['calib'][0]['Channel_off']=1
    # i2csocket.update_yamlConfig(yamlNode=nestedConf.to_dict())
    # i2csocket.configure()

    # util.saveFullConfig(odir=odir,i2c=i2csocket,daq=daqsocket,cli=clisocket)
    # util.saveMetaYaml(odir=odir,i2c=i2csocket,daq=daqsocket,runid=0,testName=testName,keepRawData=1,chip_params={})

    # util.acquire(daq=daqsocket, client=clisocket)
    mylittlenotifier.stop()
    

    # ped_analyzer = analyzer.pedestal_run_analyzer(odir=odir)
    files = glob.glob(odir+"/*.root")

    for f in files:
        print("files:",f)
        ped_analyzer.add(f)

    # ped_analyzer.mergeData()
    # ped_analyzer.makePlots()
    return odir




if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option("-d", "--dut", dest="dut",
                      help="device under test")

    parser.add_option("-i", "--hexaIP",
                      action="store", dest="hexaIP",
                      help="IP address of the zynq on the hexactrl board")

    parser.add_option("-f", "--configFile",default="./configs/init.yaml",# change the yaml file to init.yaml
                      action="store", dest="configFile",
                      help="initial configuration yaml file")

    parser.add_option("-o", "--odir",
                      action="store", dest="odir",default='./data',
                      help="output base directory")

    parser.add_option("-s", "--suffix",#============added 14022023
                      action="store", dest="suffix",default='',
                      help="output base directory")


#    parser.add_option("-t","--tileboard",
#                      action="store", dest="tileboard",default='TB2.1_3',
#                      help="tileboard in use")

    parser.add_option("-v","--overvoltage",
                      action="store", dest="OV",default='2V',
                      help="overvoltage to be used")

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

    daqsocket = zmqctrl.daqController(options.hexaIP,options.daqPort,options.configFile)
    clisocket = zmqctrl.daqController("localhost",options.pullerPort,options.configFile)
    i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort,options.configFile)
    clisocket.yamlConfig['client']['serverIP'] = options.hexaIP# added 14022023
    
    if options.initialize==True:
        i2csocket.initialize()
        daqsocket.initialize()
        clisocket.yamlConfig['client']['serverIP'] = daqsocket.ip
        clisocket.initialize()

    else:
        i2csocket.configure()
    
    read_sca_config(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.OV)
    #read_sca_config(i2csocket,daqsocket,clisocket,options.odir,options.dut,options.tileboard,options.OV)
