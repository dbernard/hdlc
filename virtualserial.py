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

    def read(self, length, timeout=None):
        '''
        Read from the channel
        '''
        return self.vs.channel_read(self.num, length, timeout=timeout)

    def write(self, data):
        '''
        Write to the channel
        '''
        self.vs.channel_write(self.num, data)


class ChannelError(Exception):
    '''
    Custom exception for channel related errors.
    '''
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'ChannelError: %s' % self.msg


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
        self.channel_queues = {}
        self._start_thread()

    def open(self, num, name=None):
        '''
        Open and return a Channel object
        '''
        return Channel(self, num, name=name)

    def add_channel(self, num):
        '''
        Add a channel to the channel buffer dict (num is the reference key)
        '''
        self.channel_queues[num] = Queue.Queue()

    def channel_read(self, chanNo, length, timeout=None):
        '''
        Read from chan_buffer for (length)
        '''
        buffdata = []
        try:
            for i in range(length):
                buffdata.append(self.channel_queues[chanNo].get(block=True,
                    timeout=timeout))
        except Queue.Empty:
            buffdata.append('')
        except KeyError:
            raise ChannelError('Could not find channel %s.' % chanNo)

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
                chanNo = ord(msg[0])
                data = msg[2:]
                self.channel_queues[chanNo].put_nowait(data)

    def _start_thread(self):
        t = threading.Thread(target = self._check_for_data)
        t.setDaemon(True)
        t.start()
        return t

