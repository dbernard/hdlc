import serial
import Queue
import hdlc
import threading

class VirtualSerial(object):
    '''
    A virtual serial connection handler for communication with the hdlc
    '''
    def __init__(self, device, numChannels):
        '''
        Start a virtual serial connection with (numChannels) channels 
        to an HDLC receiver taking to  (device).
        '''
        self.hdlc = hdlc.Receiver(device))
        self.chan_buffers = []
        for i in range(numChannels):
            self.chan_buffers.append(Queue.Queue())
        self._startThread()

    def chan_read(self, chanNo, length=1, timeout=None):
        '''
        Read from chan_buffer for (length)
        '''
        buffdata = []
        for i in range(length):
            buffdata.append(self.chan_buffers[chanNo].get(block=True,
                timeout=timeout))
        data = ''.join(buffdata)

        return data

    def chan_write(self, chanNo, data):
        '''
        Write to a channel on the hdlc
        '''
        self.hdlc.send(chanNo, 0, data)
        #channel num, cmd (0 for now), data

    def _check_for_data(self):
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

    def _start_thread(self):
        t = threading.Thread(target = self._check_for_data())
        t.setDaemon(True)
        t.start()
        return t

