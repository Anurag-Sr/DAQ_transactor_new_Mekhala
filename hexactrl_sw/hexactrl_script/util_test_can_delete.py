import yaml
import zmq_controler
from time import sleep
import glob

def acquire(daq,client):
    print("client")
    client.start()
    print("client started!")
    print("daq")
    daq.start()
    print("daq started!")
    
    print("wait until done")
    while True:
        if daq.is_done() == True:
            break
        else:
            sleep(0.01)
    print("I am here 4")
    # daq.stop()
    print("run done")
    sleep(0.01)
    print("I am here 5")
    client.stop()
    print("leaving acquire")

def mars_acquire(daq,client,odir):
    print("client")
    client.start()
    print("daq")
    daq.start()
    print("wait until done")
    while True:
        if daq.is_done() == True:
            break
        else:
            sleep(0.01)
    # daq.stop()
    print("run done")
    while True:
        roots = glob.glob(odir+"/*.root")
        yamls = glob.glob(odir+"/*.yaml")
        # print(roots,yamls)
        if len(roots)==len(yamls)-1:
            break
        sleep(0.1)    
    client.stop()
    print("leaving acquire")

def acquire_scan(daq):
    daq.start()
    while True:
        if daq.is_done() == True:
            break
        else:
            sleep(0.01)
    # daq.stop()

def saveFullConfig(odir,i2c,daq,cli):
    ret=i2c.read_config()


    #test by Jia-Hao
    print("")
    print("def saveFullConfig, ret=i2c.read_config from util.py  def saveFullConfig")
    print("")
    print(ret)
    print("")
    #test end

    for key in ret.keys():
       if key.find('roc_s')==0:
           i2c.yamlConfig[key] = { 'sc': ret[key] }

           #test by Jia-Hao
           print("")
           print("for key in ret.keys from util.py   def saveFullConfig")
           print("")
           print(key)

           print("")
           print("i2c.yamlConfig[key] = { 'sc': ret[key]  from util.py   def saveFullConfig")
           print("")
           print(i2c.yamlConfig[key])
           print("")
           #test end
    
    initial_full_config={}
    for key in i2c.yamlConfig.keys():

        #test by Jia-Hao
        print("")
        print("for key in i2c.yamlConfig.keys from util.py   def saveFullConfig")
        print("")
        print(key)
        print("")
        #test end


        if key.find('roc_s')==0:
            initial_full_config[key] = i2c.yamlConfig[key]
            print("")
            print("initial_full_config[key] = i2c.yamlConfig[key from util.py   def saveFullConfig")
            print("")
            print(initial_full_config[key])
            print("")


    initial_full_config['daq'] = daq.yamlConfig['daq']
    print("")
    print("initial_full_config['daq'] = daq.yamlConfig['daq from util.py   def saveFullConfig")
    print("")
    print(initial_full_config['daq'])
    print("")

    initial_full_config['client'] = cli.yamlConfig['client']

    print("")
    print("initial_full_config['client'] = cli.yamlConfig['client from util.py   def saveFullConfig")
    print("")
    print(initial_full_config['client'])
    print("")
    
    with open(odir+"/initial_full_config.yaml",'w') as fout:
        yaml.dump(initial_full_config,fout)
    print("")
    print("The final init full config is from util.py   def saveFullConfig")
    print("")
    print(initial_full_config)
    print("")

    
def saveMetaYaml(odir,i2c,daq,runid=0,testName='undefined',keepRawData=0,chip_params={},characMode=1,keepSummary=1):
    meta_yaml={}
    ndaqlinks = len(daq.yamlConfig['daq']['elinks_daq'])
    meta_yaml['metaData']={}
    meta_yaml['metaData']['hexactrl']            = i2c.ip
    meta_yaml['metaData']['hw_type']             = '1ROC' if ndaqlinks==2 else 'LD' if ndaqlinks==6 else 'HD'if ndaqlinks==12 else 'unknown'
    meta_yaml['metaData']['testName']            = testName
    meta_yaml['metaData']['keepRawData']         = keepRawData
    meta_yaml['metaData']['keepSummary']         = keepSummary
    meta_yaml['metaData']['Channel_off']         = i2c.maskedDetIds
    meta_yaml['metaData']['chip_params']         = chip_params
    print("now print yamlConfig['roc_s0']:")
    print(i2c.yamlConfig['roc_s0'])
    #meta_yaml['metaData']['characMode']          = i2c.yamlConfig['roc_s0']['sc']['DigitalHalf'][0]['CalibrationSC'] if 'CalibrationSC' in i2c.yamlConfig['roc_s0']['sc']['DigitalHalf'][0] else i2c.yamlConfig['roc_s1']['sc']['DigitalHalf'][0]['CalibrationSC'] if 'CalibrationSC' in i2c.yamlConfig['roc_s1']['sc']['DigitalHalf'][0] else i2c.yamlConfig['roc_s2']['sc']['DigitalHalf'][0]['CalibrationSC'] if 'CalibrationSC' in i2c.yamlConfig['roc_s2']['sc']['DigitalHalf'][0] else 0
    meta_yaml['metaData']['characMode']          = i2c.yamlConfig['roc_s0']['sc']['DigitalHalf'][0]['CalibrationSC'] if 'CalibrationSC' in i2c.yamlConfig['roc_s0']['sc']['DigitalHalf'][0] else 0
    with open(odir + "/" + testName + str(runid) + '.yaml', 'w') as fout:
        yaml.dump(meta_yaml, fout)
    
