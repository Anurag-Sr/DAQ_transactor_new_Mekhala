import zmq_controller as zmqctrl

def create_socket(ipAddress, port=5555):
    i2csocket = zmqctrl.i2cController(options.hexaIP,options.i2cPort)

def configure(i2csocket: i2cController, configuration)
    i2csocket.configure(configuration)
    
def get_configuration(i2csocket: i2cController):
    pass
    
    
def set_mppc_bias_voltage():
