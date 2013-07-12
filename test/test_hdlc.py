import unittest

import hdlc


class FakeDevice(object):
    def __init__(self, data):
        self.data = list(data)

    def read(self, count):
        assert count == 1
        if len(self.data) == 0:
            return None
        return self.data.pop(0)


def _make_receiver(data):
    return hdlc.Receiver(FakeDevice(data))


class TestHdlc(unittest.TestCase):
    def test_unframed(self):
        r = _make_receiver('bad')
        self.assertEqual(r.get(), None)
        self.assertEqual(r.statistics['bytes'], 3)
        self.assertEqual(r.statistics['unframed'], 3)

    def test_empty(self):
        r = _make_receiver('\x7e\x7e')
        self.assertEqual(r.get(), None)
        self.assertEqual(r.statistics['bytes'], 2)
        self.assertEqual(r.statistics['empty'], 1)

    def test_short(self):
        r = _make_receiver('\x7ebad\x7e')
        self.assertEqual(r.get(), None)
        self.assertEqual(r.statistics['bytes'], 5)
        self.assertEqual(r.statistics['invalid'], 1)

    def test_escaped(self):
        r = _make_receiver('\x7eabc\x7d\x5edef\x7e')
        self.assertEqual(r.get(), 'abc\x7edef')
        self.assertEqual(r.statistics['bytes'], 10)
