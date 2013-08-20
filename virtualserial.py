import serial
import hdlc
import threading

class VirtualSerial(object):
    '''
    A virtual serial connection handler for communication wit the hdlc
    '''
    def __init__(self, serPort, numChannels):
        self.hdlc = hdlc.Receiver(port=serPort)
        self.chan_buffers = []
        for i in range(numChannels):
            # Look into queues insteat of lists
            self.chan_buffers.append([])
        self._startRxThread()

    def chanRead(self, chanNo, length):
        # Read from chan_buffer for (length)
        pass

    def chanWrite(self, chanNo, data):
        # Adjust send to match this format
        self.hdlc.send(chanNo, 0, data) #channel num, command, data

    def _checkForData(self):
        while True:
            # Do something about empty data - Dont fill buffer with empty data
            msg = hdlc.get()
            # (channel num)(cmd num)(data)
            chanNo = ord(msg[0])
            self.chan_buffers[chanNo].append(msg[2:])

    def _startRxThread(self):
        t = threading.Thread(target = self._checkForData())
        t.setDaemon(True)
        t.start()
        return t

