import telnetlib
import math
import logging
import time

logging.basicConfig(level=logging.INFO)

from enum import Enum


class TableController():
    #positive direction is away from the motor
    HCONTROL = "Z01"
    VCONTROL = "Z00"

    def __init__(self,ip="192.168.1.66", port="8000", timeout=1):
        self._ip = ip
        self._port = port
        self._timeout = timeout
        self._session = None
        
    def connect(self):
        if self._session==None:
            self._session = telnetlib.Telnet(self._ip, self._port, self._timeout)
        else:
            logging.error("Cannot connect since previous session is still open")
        
    def disconnect(self):
        if self._session==None:
            logging.error("Cannot disconnect since previous session is still open")
        else:
            self._session.close()
            self._session = None
            
    def read_value(self,component):
        self._session.write((component+"H\r").encode("ascii"))
        data = self._session.read_until(b"@",self._timeout).decode("ascii")
        logging.debug("receive data:"+data)
        data = self._session.read_until(b"@",self._timeout).decode("ascii")
        value = float(data[3:-1])*0.1
        logging.debug("receive data:"+data)
        logging.debug("decoded value:"+str(value))
        return value 
        
    def block_while_moving(self, component, nvalues_to_check = 5, delay=0.2, max_iter=1000):
        previous_values = []
        for idx in range(max_iter):
            logging.debug("wait iteration:"+str(idx))
            time.sleep(delay)
            current_value = self.read_value(component)
            logging.info("current value while moving:"+str(current_value))
            if len(previous_values)<nvalues_to_check:
                previous_values.append(current_value)
                logging.debug("added value")
            else:
                previous_values[idx%nvalues_to_check] = current_value
                distance = math.fabs(previous_values[(idx+1)%nvalues_to_check]-current_value)
                logging.debug("distance to last value: "+str(distance))
                if distance<0.1:
                    logging.info("movement stopped")
                    return True
                    
        return False
                
    def set_value(self,component,value):
        encodedValue = "%+07d"%(round(value*10.))
        logging.debug("sending value:"+str(encodedValue))
        self._session.write((component+"B"+encodedValue+"\r").encode("ascii"))
        self._session.write((component+"U\r").encode("ascii"))
        self.block_while_moving(component)
        
    def get_vertical(self):
        return self.read_value(TableController.VCONTROL)
    
    def get_horizontal(self):
        return self.read_value(TableController.HCONTROL)
        
    def move_vertical(self,value):
        self.set_value(TableController.VCONTROL,value)

    def move_horizontal(self,value):
        self.set_value(TableController.HCONTROL,value)
        
    def move_optimized(self,
        compontent, value, 
        acceptance_distance=0.1, #read value needs to be within this distance to the target value
        readjust_distance=2., #if target value to close to current one need to move away first
        moveaway_distance=10. #distance to move away if values are too close
    ):
        currentValue = self.get_value(component)
        if math.fabs(value-currentValue)<=acceptance_distance:
            return #already in position
        if math.fabs(value-currentValue)<=readjust_distance: #need to move away
            pass
        

#hitting TB ch37/39/38/39: h=', 325.1, 'v=', -665.0
#hitting ch36: 'h=', 303.9, 'v=', -639.9 
