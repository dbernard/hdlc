import unittest

from virtualserial import *

class FakeDevice(object):
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
    def test_emptyBufferRead(self):
        vs = VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        self.assertEqual(vs.channel_read(0, 1, timeout=1), '')

    def test_singleEntryBufferRead(self):
        vs = VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.channel_write(0, 'foo')
        self.assertEqual(vs.channel_read(0, 3), 'foo')

    def test_multiEntryBufferRead(self):
        vs = VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.channel_write(0, 'foo')
        vs.channel_write(0, 'bar')
        self.assertEqual(vs.channel_read(0, 6), 'foobar')

    def test_multiChannelBufferRead(self):
        vs = VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.add_channel(num=1)
        vs.channel_write(0, 'foo')
        vs.channel_write(1, 'bar')
        self.assertEqual(vs.channel_read(0, 3), 'foo')
        self.assertEqual(vs.channel_read(1, 3), 'bar')

    def test_addChannel(self):
        vs = VirtualSerial(FakeDevice())
        self.assertEqual(len(vs.channel_queues), 0)
        vs.add_channel(num=0)
        self.assertEqual(len(vs.channel_queues), 1)


class testChannel(unittest.TestCase):
    def test_initializeChannel(self):
        vs = VirtualSerial(FakeDevice())
        ch = Channel(vs, num=0, name='test')
        self.assertEqual(ch.name, 'test')
        self.assertEqual(ch.num, 0)

    def test_channelWriteRead(self):
        vs = VirtualSerial(FakeDevice())
        ch = Channel(vs, num=0)
        ch.write('foo')
        self.assertEqual(ch.read(3), 'foo')

    def test_open(self):
        vs = VirtualSerial(FakeDevice())
        ch = vs.open(num=0, name='test')
        ch.write('foo')
        self.assertEqual(ch.num, 0)
        self.assertEqual(ch.name, 'test')
        self.assertEqual(ch.read(3), 'foo')

    def test_channelError(self):
        vs = VirtualSerial(FakeDevice())
        with self.assertRaises(ChannelError):
            vs.channel_read(0, 1)


