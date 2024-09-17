import zmq
import yaml
import typing
import os
from time import sleep
from nested_dict import nested_dict

def merge(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

class zmqController:
    def __init__(self, ip:str, port:int):
        self.context = zmq.Context()
        self.ip=ip
        self.port=port
        self.connect()
        
    def connect(self):
        self.socket = self.context.socket( zmq.REQ )
        self.socket.connect("tcp://"+str(ip)+":"+str(port))

    def reset(self):
        self.socket.close()
        self.reset()
          
    def send_command(self, command: str, data: 'typing.Optional[str]' = None) -> str:
        if data is None:
            self.socket.send_string(command)
        else:
            self.socket.send_string(command,zmq.SNDMORE)
            self.socket.send_string(data)
        reply = self.socket.recv_string() #replies should always be send as strings not bytes
        try:
            config = yaml.safe_load(reply) #does nothing to pure strings
            return config
        except yaml.YAMLError as e:
            print (f"ERROR: Slow control server replies with non valid str/yaml '{reply}'") 
        return reply
          

#this class should have methods matching the commands accepted by zmq_server.py
#note that there is NO difference between 'initialize' and 'configure' on the zmq_server side
class i2cController(zmqController):    
    def __init__(self, ip, port=5555):
        super(i2cController, self).__init__(ip,port)
        
    def initialize(self, config: 'dict[typing.Any, typing.Any]') -> str:
        return self.send_command("initialize",yaml.dump(config))
        
    def initialize_from_file(self, fname: 'typing.Union[str, bytes, os.PathLike]') -> str:
        with open(fname) as fin:
            config=yaml.safe_load(fin)
        return self.initialize(config)

    def configure(self, config: 'dict[typing.Any, typing.Any]') -> str:
        return self.send_command("configure",yaml.dump(config))
        
    def configure_from_file(self, fname: 'typing.Union[str, bytes, os.PathLike]') -> str:
        with open(fname) as fin:
            config=yaml.safe_load(fin)
        return self.configure(config)
        					
    def read(self):
        return self.send_command("read","")
		
    def read_pwr(self):
        ## only valid for hexaboard/trophy systems
        return self.send_command("read_pwr")
        
    def resettdc(self):
        return self.send_command("resettdc")
       
    def set_gbtsca_dac(self,dac,val):
        return self.send_command("set_gbtsca_dac "+str(dac)+" "+str(val))

    def read_gbtsca_dac(self,dac):
        return self.send_command("read_gbtsca_dac "+str(dac))

    def read_gbtsca_adc(self,channel):
        return self.send_command("read_gbtsca_adc "+str(channel))
 
    def read_gbtsca_gpio(self):
        return self.send_command("read_gbtsca_gpio")

    def set_gbtsca_gpio_direction(self,direction):
        return self.send_command("set_gbtsca_gpio_direction "+str(direction))

    def get_gbtsca_gpio_direction(self):
        return self.send_command("get_gbtsca_gpio_direction")

    def set_gbtsca_gpio_vals(self,vals,mask):
        return self.send_command("set_gbtsca_gpio_vals "+str(vals)+" "+str(mask))

    def measadc(self,yamlNode):
        ## only valid for hexaboard/trophy systems
        self.socket.send_string("measadc",zmq.SNDMORE)
        # rep = self.socket.recv_string()
        # if rep.lower().find("ready")<0:
        #     print(rep)
        #     return
        if yamlNode:
            config=yamlNode
        else:
            config = self.yamlConfig
        self.socket.send_string(yaml.dump(config))
        rep = self.socket.recv_string()
        adc = yaml.safe_load(rep)
        return( adc )

    '''
    def sipm_configure_injection(self,injectedChannels, activate=0, gain=0, phase=None, calib_dac=0):
        nestedConf = nested_dict()
        for key in self.yamlConfig.keys():
            if key.find('roc_s')==0:
                nestedConf[key]['sc']['ReferenceVoltage']['all']['IntCtest'] = 0
                nestedConf[key]['sc']['ReferenceVoltage']['all']['choice_cinj'] = 0
                if gain < 2:
                    nestedConf[key]['sc']['ReferenceVoltage']['all']['cmd_120p'] = gain
                if calib_dac == -1:
                    nestedConf[key]['sc']['ReferenceVoltage']['all']['Calib_2V5'] = 0
                else:
                    nestedConf[key]['sc']['ReferenceVoltage']['all']['Calib_2V5'] = calib_dac
                if not None==phase: # no default phase, we don't change when not set
                    nestedConf[key]['sc']['Top']['all']['phase_ck'] = phase
                if not None==injectedChannels:
                    for injectedChannel in injectedChannels:
                        nestedConf[key]['sc']['ch'][injectedChannel]['HighRange'] = activate
                        nestedConf[key]['sc']['ch'][injectedChannel]['LowRange'] = 0
        self.configure(yamlNode=nestedConf.to_dict())
        if not None==phase:
            self.resettdc()	# Reset MasterTDCs

    def configure_injection(self,injectedChannels, activate=0, gain=0, phase=None, calib_dac=0):
        nestedConf = nested_dict()
        for key in self.yamlConfig.keys():
            if key.find('roc_s')==0:
                if calib_dac == -1:
                    nestedConf[key]['sc']['ReferenceVoltage']['all']['IntCtest']=0
                else:
                    nestedConf[key]['sc']['ReferenceVoltage']['all']['IntCtest'] = activate
                    nestedConf[key]['sc']['ReferenceVoltage']['all']['Calib'] = calib_dac
                if not None==phase: # no default phase, we don't change when not set
                    nestedConf[key]['sc']['Top']['all']['phase_ck'] = phase
                for injectedChannel in injectedChannels:
                    nestedConf[key]['sc']['ch'][injectedChannel]['LowRange'] = 0
                    nestedConf[key]['sc']['ch'][injectedChannel]['HighRange'] = 0
                    if gain==0:
                        nestedConf[key]['sc']['ch'][injectedChannel]['LowRange'] = activate
                    else:
                        nestedConf[key]['sc']['ch'][injectedChannel]['HighRange'] = activate
        self.configure(yamlNode=nestedConf.to_dict())
        if not None==phase:
            self.resettdc()	# Reset MasterTDCs
    '''
    
#this class should have methods matching the commands accepted by zmq_server.py
class daqController(zmqController):
    def start(self):
        status="none"
        while status.lower().find("running")<0: 
            self.socket.send_string("start")
            status = self.socket.recv_string()
            print(status)

    def is_done(self):
        self.socket.send_string("status")
        status = self.socket.recv_string()
        if status.lower().find("configured")<0:
            return False
        else:
            return True

    def delay_scan(self):
        # only for daq server to run a delay scan
        rep=""
        while rep.lower().find("delay_scan_done")<0: 
            self.socket.send_string("delayscan")
            rep = self.socket.recv_string()
        print(rep)
	
    def stop(self):
        self.socket.send_string("stop")
        rep = self.socket.recv_string()
        print(rep)
        
    def enable_fast_commands(self,random=0,external=0,sequencer=0,ancillary=0):
        self.yamlConfig['daq']['l1a_enables']['random_l1a']         = random
        self.yamlConfig['daq']['l1a_enables']['external_l1as']      = external
        self.yamlConfig['daq']['l1a_enables']['block_sequencer']    = sequencer

    def l1a_generator_settings(self,name='A',enable=0x0,BX=0x10,length=43,flavor='L1A',prescale=0,followMode='DISABLE'):
        for gen in self.yamlConfig['daq']['l1a_generator_settings']:
            if gen['name']==name:
                gen['BX']         = BX
                gen['enable']     = enable
                gen['length']     = length
                gen['flavor']     = flavor
                gen['prescale']   = prescale
                gen['followMode'] = followMode
        
    def l1a_settings(self,bx_spacing=43,external_debounced=0,ext_delay=0,prescale=0,log2_rand_bx_period=0):#,length=43
        self.yamlConfig['daq']['l1a_settings']['bx_spacing']          = bx_spacing
        self.yamlConfig['daq']['l1a_settings']['external_debounced']  = external_debounced
        # self.yamlConfig['daq']['l1a_settings']['length']              = length
        self.yamlConfig['daq']['l1a_settings']['ext_delay']           = ext_delay
        self.yamlConfig['daq']['l1a_settings']['prescale']            = prescale
        self.yamlConfig['daq']['l1a_settings']['log2_rand_bx_period'] = log2_rand_bx_period
        
    def ancillary_settings(self,bx=0x10,prescale=0,length=100):
        self.yamlConfig['daq']['ancillary_settings']['bx']       = bx
        self.yamlConfig['daq']['ancillary_settings']['prescale'] = prescale
        self.yamlConfig['daq']['ancillary_settings']['length']   = length
            
