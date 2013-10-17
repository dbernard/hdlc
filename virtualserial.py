import serial
import Queue
import hdlc
import threading

from collections import deque


class VSQueue(Queue.Queue):
    def extend(self, item, block=True, timeout=None):
        '''
        Put an item into the queue using extend to break the item up. Please
        note, this implementation does not account for checking the maxsize (if
        applicable) of a Queue if an item will extend beyond capacity. Perform
        this check elsewhere. This will, however, protect against the case where
        a Queue is at its exact capacity.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        '''
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
            self._extend(item)
            self.unfinished_tasks += len(item)
            self.not_empty.notify()
        finally:
            self.not_full.release()

    def _extend(self, item):
        self.queue.extend(item)


class Channel(object):
    '''
    An object representing a virtual serial channel.
    '''
    def __init__(self, vsObj, num, name=None, maxsize=0):
        self.vs = vsObj
        self.num = num
        self.name = name
        self.vs.add_channel(num, maxsize=maxsize)

    def read(self, length, timeout=None):
        '''
        Read from the channel for (length) bytes.
        '''
        return self.vs.channel_read(self.num, length, timeout=timeout)

    def write(self, data):
        '''
        Write (data) to the channel.
        '''
        self.vs.channel_write(self.num, data)

    def isFull(self):
        '''
        Return True if the channel is full, False if it is not.
        '''
        return self.vs.channel_queues[self.num].full()

    def isEmpty(self):
        '''
        Return True if the channel is empty, False if it is not.
        '''
        return self.vs.channel_queues[self.num].empty()


class ChannelError(Exception):
    '''
    Custom exception for channel related errors.
    '''
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return '%s' % self.msg


class VirtualSerial(object):
    '''
    A virtual serial connection handler for communication with the HDLC.
    '''
    def __init__(self, device):
        '''
        Start a virtual serial connection with (numChannels) channels
        to an HDLC receiver connected to (device).
        '''
        self.hdlc = hdlc.Receiver(device)
        self.channel_queues = {}
        self._start_thread()

    def open(self, num, name=None, maxsize=0):
        '''
        Open and return a Channel object.
        '''
        return Channel(self, num, name=name, maxsize=maxsize)

    def add_channel(self, num, maxsize=0):
        '''
        Add a channel to the channel queues dict (num is the reference key).
        '''
        self.channel_queues[num] = VSQueue(maxsize=maxsize)

    def channel_read(self, chanNo, bytes, timeout=None):
        '''
        Read from channel_queues for (bytes) bytes. The bytes read are joined
        and returned as a single piece of data.
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
        Write to a channel on the HDLC.
        '''
        self.hdlc.send(chanNo, 0, data)
        #channel num, control (0 for now), data

    def _check_for_data(self):
        '''
        Continuously check for incoming data - break it up and add it to the
        queue.

        If the queues have a size limit and either the queue is full or
        the incoming data will surpass the size limit, add enough data to the
        queue to fill it, then hang on to the rest of the data until it can be
        added.
        '''
        while True:
            msg = self.hdlc.get()
            if msg:
                # (channel num)(cmd num)(data)
                chanNo = ord(msg[0])
                data = msg[2:]
                targetQueue = self.channel_queues[chanNo]
                if targetQueue.maxsize > 0:
                    while data:
                        # We only expect a single writer per queue, so 
                        # qsize() should be accurate.
                        free = targetQueue.maxsize - targetQueue.qsize()
                        if free:
                            targetQueue.extend(data[:free], False)
                        data = data[free:]
                else:
                    targetQueue.extend(data, False)

    def _start_thread(self):
        t = threading.Thread(target = self._check_for_data)
        t.setDaemon(True)
        t.start()
        return t

