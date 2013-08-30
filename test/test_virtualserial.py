import unittest

import virtualserial

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
        vs = virtualserial.VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        self.assertEqual(vs.channel_read(0, timeout=1), '')

    def test_singleEntryBufferRead(self):
        vs = virtualserial.VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.channel_write(0, 'hello')
        self.assertEqual(vs.channel_read(0), 'hello')

    def test_multiEntryBufferRead(self):
        vs = virtualserial.VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.channel_write(0, 'foo')
        vs.channel_write(0, 'bar')
        self.assertEqual(vs.channel_read(0, length=2), 'foobar')

    def test_multiChannelBufferRead(self):
        vs = virtualserial.VirtualSerial(FakeDevice())
        vs.add_channel(num=0)
        vs.add_channel(num=1)
        vs.channel_write(0, 'foo')
        vs.channel_write(1, 'bar')
        self.assertEqual(vs.channel_read(0), 'foo')
        self.assertEqual(vs.channel_read(1), 'bar')

    def test_addChannel(self):
        vs = virtualserial.VirtualSerial(FakeDevice())
        self.assertEqual(len(vs.chan_buffers), 0)
        vs.add_channel(num=0)
        self.assertEqual(len(vs.chan_buffers), 1)


class testChannel(unittest.TestCase):
    def test_initializeChannel(self):
        vs = virtualserial.VirtualSerial(FakeDevice())
        ch = virtualserial.Channel(vs, num=0, name='test')
        self.assertEqual(ch.name, 'test')
        self.assertEqual(ch.num, 0)

    def test_channelWriteRead(self):
        vs = virtualserial.VirtualSerial(FakeDevice())
        ch = virtualserial.Channel(vs, num=0)
        ch.write('foo')
        self.assertEqual(ch.read(), 'foo')

    def test_open(self):
        vs = virtualserial.VirtualSerial(FakeDevice())
        ch = virtualserial.open(vs, num=0, name='test')
        self.assertEqual(ch.num, 0)
        self.assertEqual(ch.name, 'test')

