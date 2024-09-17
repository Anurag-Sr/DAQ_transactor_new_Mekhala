import zmq
import yaml
from Link import LinkBuilder
import Boards

""" ZMQ-Server: Redirect user request to Board. """

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
print('[ZMQ] Server started')

def redirect(fn):
    cfg_str  = socket.recv_string()
    cfg_yaml = yaml.safe_load(cfg_str)
    ans_yaml = fn(cfg_yaml)
    ans_str  = yaml.dump(ans_yaml, default_flow_style=False)
    socket.send_string(ans_str)

try:
    linkbuilder = LinkBuilder()
    links = linkbuilder.links
    if len(links) == 1: board = Boards.CharBoard(links)
    if len(links) >= 3: board = Boards.HexaBoard(links)

    while True:
        string = socket.recv_string().lower()
        splitstring = string.split(" ")

        if string == "initialize":
            if len(links) == 1: board = Boards.CharBoard(links)
            elif len(links) >= 2: board = Boards.HexaBoard(links)
            if board: redirect(board.configure)
            else: socket.send_string("error: could not initialize I2C server")

        elif string == "configure":
            if board: redirect(board.configure)
            else: socket.send_string("error: board was not initialized")

        elif string == "read": redirect(board.read)

        elif string == "reset_tdc" or string == "resettdc":
            ans = board.reset_tdc()
            socket.send_string('%s' % ans)

        elif string == "read_adc" or string == "measadc":
            if type(board) is Boards.HexaBoard: redirect(board.read_adc)
            else: socket.send_string('error: ADCs exist only on Trophy/Hexaboard.')

        elif string == "read_pwr":
            if type(board) is Boards.HexaBoard:
                pwr = board.read_pwr()
                socket.send_string("%s" % yaml.dump(pwr, default_flow_style=False))
            else: socket.send_string('error: ADCs exist only on Trophy/Hexaboard.')

        elif splitstring[0] == "set_gbtsca_dac":
            dac_str = splitstring[1]
            val_str = splitstring[2]
            linkbuilder.sca.dacWrite(dac_str,val_str)
            socket.send_string("Done setting gbtsca dac "+str(dac_str)+" to "+str(val_str))

        elif splitstring[0] == "read_gbtsca_dac":
            dac_str = splitstring[1]
            dac_val = linkbuilder.sca.dacRead(dac_str)
            socket.send_string(str(dac_val))

        elif splitstring[0] == "read_gbtsca_adc":
            channel_str = splitstring[1]
            adc_val = linkbuilder.sca.adcRead(int(channel_str))
            socket.send_string(str(adc_val))
 
        elif string == "read_gbtsca_gpio":
            gpio_vals = linkbuilder.sca.gpioRead()
            socket.send_string(str(gpio_vals))
 
        elif splitstring[0] == "set_gbtsca_gpio_direction":
            gpio_directions = splitstring[1]
            linkbuilder.sca.gpioSetDirection(int(gpio_directions))
            socket.send_string("Done setting gpio directon to "+str(gpio_directions))
 
        elif string == "get_gbtsca_gpio_direction":
            gpio_vals = linkbuilder.sca.gpioGetDirection()
            socket.send_string(str(gpio_vals))

        elif splitstring[0] == "set_gbtsca_gpio_vals":
            gpio_vals = splitstring[1]
            gpio_mask = splitstring[2] 
            linkbuilder.sca.gpioWrite(int(gpio_vals),int(gpio_mask))
            socket.send_string("Done setting gpio values to "+str(gpio_vals)+" with mask "+str(gpio_mask))

except KeyboardInterrupt:
    print('\nClosing server.')
    socket.close()
    context.term()
