import serial
import Queue
import hdlc
import threading

class Channel(object):
    '''
    An object representing a virtual serial channel
    '''
    def __init__(self, vsObj, num, name=None):
        self.vs = vsObj
        self.num = num
        self.name = name
        self.vs.add_channel(num)

    def read(self, length=1, timeout=None):
        '''
        Read from the channel
        '''
        return self.vs.channel_read(self.num, length=length, 
                timeout=timeout)

    def write(self, data):
        '''
        Write to the channel
        '''
        self.vs.channel_write(self.num, data)

def open(vsObj, num, name=None):
    '''
    Open and return a Channel object
    '''
    return Channel(vsObj, num, name=name)


class VirtualSerial(object):
    '''
    A virtual serial connection handler for communication with the hdlc
    '''
    def __init__(self, device):
        '''
        Start a virtual serial connection with (numChannels) channels 
        to an HDLC receiver taking to  (device).
        '''
        self.hdlc = hdlc.Receiver(device)
        self.chan_buffers = {}
        self._start_thread()

    def add_channel(self, num):
        '''
        Add a channel to the channel buffer dict (num is the reference key)
        '''
        self.chan_buffers[num] = Queue.Queue()

    def channel_read(self, chanNo, length=1, timeout=None):
        '''
        Read from chan_buffer for (length)
        '''
        buffdata = []
        try:
            for i in range(length):
                buffdata.append(self.chan_buffers[chanNo].get(block=True,
                    timeout=timeout))
        except Queue.Empty:
            buffdata.append('')

        data = ''.join(buffdata)

        return data

    def channel_write(self, chanNo, data):
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
            msg = self.hdlc.get()
            if msg:
                # (channel num)(cmd num)(data)
                chanNo = int(msg[0])
                data = msg[2:]
                self.chan_buffers[chanNo].put_nowait(data)

    def _start_thread(self):
        t = threading.Thread(target = self._check_for_data)
        t.setDaemon(True)
        t.start()
        return t

