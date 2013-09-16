import unittest
import time

from virtualserial import *

class FakeDevice(object):
    '''
    A fake device for testing purposes. Reroutes all input from the write
    function to output from the read function.
    '''
    def __init__(self):
        self.data = []

    def read(self, count):
        assert count == 1
        if len(self.data) == 0:
            return None

        return self.data.pop(0)

    def write(self, data):
        for character in data:
            self.data.append(character)


class TestVirtualSerial(unittest.TestCase):
    def test_emptyQueueRead(self):
        '''
        Verify no data is read from an empty queue and no exceptions are raised.
        '''
        vs = VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        self.assertEqual(vs.channel_read(0, 1, timeout=1), '')

    def test_singleEntryQueueRead(self):
        '''
        Verify a single data entry into a Queue is read correctly.
        '''
        vs = VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.channel_write(0, 'foo')
        self.assertEqual(vs.channel_read(0, 3), 'foo')

    def test_multiEntryQueueRead(self):
        '''
        Verify multiple data entries in the same Queue are read correctly.
        '''
        vs = VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.channel_write(0, 'foo')
        vs.channel_write(0, 'bar')
        self.assertEqual(vs.channel_read(0, 6), 'foobar')

    def test_multiChannelQueueRead(self):
        '''
        Verify entries on multiple channels are read correctly.
        '''
        vs = VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.add_channel(num=1)
        vs.channel_write(0, 'foo')
        vs.channel_write(1, 'bar')
        self.assertEqual(vs.channel_read(0, 3), 'foo')
        self.assertEqual(vs.channel_read(1, 3), 'bar')

    def test_addChannel(self):
        '''
        Verify that adding a channel to a channel-less VS instance increments
        the number of available channels.
        '''
        vs = VirtualSerial(FakeDevice())
        self.assertEqual(len(vs.channel_queues), 0)
        vs.add_channel(num=0)
        self.assertEqual(len(vs.channel_queues), 1)

    def test_fullChannelQueue(self):
        '''
        Verify that a channel will write only enough data to fill itself and
        hang on to the remaining data until room has been made for it.
        '''
        vs = VirtualSerial(FakeDevice())
        ch = vs.open(num=0, maxsize=5)
        ch.write('foo')
        ch.write('bar')
        while not ch.isFull():
            pass
        assert ch.isFull()
        # Verify that reading the full length of the queue included parts of the
        # second write
        self.assertEqual(ch.read(5), 'fooba')
        # Verify that emptying out the queue allowed the last item to be placed
        self.assertEqual(ch.read(1), 'r')
        # Verify that the queue is now empty
        while not ch.isEmpty():
            pass
        assert ch.isEmpty()


class testChannel(unittest.TestCase):
    def test_initializeChannel(self):
        '''
        Verify that a channel is appropriately initialized with given
        properties.
        '''
        vs = VirtualSerial(FakeDevice())
        ch = Channel(vs, num=0, name='test')
        self.assertEqual(ch.name, 'test')
        self.assertEqual(ch.num, 0)

    def test_channelWriteRead(self):
        '''
        Verify that writing to a channel and reading from a channel yield an
        expected result.
        '''
        vs = VirtualSerial(FakeDevice())
        ch = Channel(vs, num=0)
        ch.write('foo')
        self.assertEqual(ch.read(3), 'foo')

    def test_open(self):
        '''
        Verify that the VS open function initializes a Channel object
        appropriately.
        '''
        vs = VirtualSerial(FakeDevice())
        ch = vs.open(num=0, name='test')
        ch.write('foo')
        self.assertEqual(ch.num, 0)
        self.assertEqual(ch.name, 'test')
        self.assertEqual(ch.read(3), 'foo')

    def test_channelReadError(self):
        '''
        Verify that a ChannelError is received when reading from a non existent
        channel.
        '''
        vs = VirtualSerial(FakeDevice())
        with self.assertRaises(ChannelError):
            vs.channel_read(0, 1)


