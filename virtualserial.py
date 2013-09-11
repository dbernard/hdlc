import serial
import Queue
import hdlc
import threading

from collections import deque


class VSQueue(Queue.Queue):
    def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        """
        self.not_full.acquire()
        try:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() == self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() == self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    endtime = _time() + timeout
                    while self._qsize() == self.maxsize:
                        remaining = endtime - _time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            self._iterput(item)
            self.unfinished_tasks += len(item)
            self.not_empty.notify()
        finally:
            self.not_full.release()

    def _iterput(self, item):
        self.queue.extend(item)


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
        self.channel_queues[num] = VSQueue()

    def channel_read(self, chanNo, bytes, timeout=None):
        '''
        Read from chan_buffer for (bytes) bytes
        '''
        buffdata = []
        try:
            for i in range(bytes):
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
        #channel num, control (0 for now), data

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

