import serial
import hdlc

class VirtualSerial(object):
    '''
    A virtual serial connection handler for communication wit the hdlc
    '''
    def __init__(self, address):
        self.conn = hdlc.Receiver(serial.Serial(port=address))

    def read(self):
        data = self.conn.get()

        if data is None:
            pass #Error? Warning? Nothing?

        return data

    def write(self, data):
        self.conn.send(data)

