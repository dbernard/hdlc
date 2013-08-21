import serial
import Queue
import hdlc
import threading

class VirtualSerial(object):
    '''
    A virtual serial connection handler for communication with the hdlc
    '''
    def __init__(self, serPort, numChannels):
        '''
        Start a virtual serial connection with (numChannels) channels 
        to an HDLC receiver at (serPort).
        '''
        self.hdlc = hdlc.Receiver(port=serPort)
        self.chan_buffers = []
        for i in range(numChannels):
            self.chan_buffers.append(Queue.Queue())
        self._startRxThread()

    def chanRead(self, chanNo, length=1, timeout=None):
        '''
        Read from chan_buffer for (length)
        '''
        buffdata = []
        for i in range(length):
            buffdata.append(self.chan_buffers[chanNo].get(block=True,
                timeout=timeout))
        data = ''.join(buffdata)

        return data

    def chanWrite(self, chanNo, data):
        '''
        Write to a channel on the hdlc
        '''
        self.hdlc.send(chanNo, 0, data)
        #channel num, cmd (0 for now), data

    def _checkForData(self):
        '''
        Continuously check for incoming data - break it up and add it to the
        queue.
        '''
        while True:
            msg = hdlc.get()
            if msg:
                # (channel num)(cmd num)(data)
                chanNo = ord(msg[0])
                data = msg[2:]
                for bit in data:
                    self.chan_buffers[chanNo].put_nowait(bit)

    def _startRxThread(self):
        t = threading.Thread(target = self._checkForData())
        t.setDaemon(True)
        t.start()
        return t

