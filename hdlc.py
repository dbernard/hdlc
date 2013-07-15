from collections import deque


class State(object):
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return self._name

    def __repr__(self):
        return '<State {0}>'.format(self._name)

    def __hash__(self):
        return hash(repr(self))


OUT_OF_SYNC = State("Out-of-Sync")
IDLE = State("Idle")
GET_FRAME = State("Get Frame")
GET_ESC = State("Get Esc")

HDLC_IDLE = '\xFF'
HDLC_FLAG = '\x7E'
HDLC_ESC = '\x7D'
HDLC_ESC_MOD = 0x20


def create_statistics():
    return {
        'bytes': 0,
        'unframed': 0,
        'empty': 0,
        'escaped_flag': 0,
        'double_escape': 0,
        'timeout': 0,
        'invalid': 0,
    }


class Receiver(object):
    '''
    HDLC Receiver

    States
    ------

    OUT_OF_SYNC:
      0x7E -> GET_FRAME
      * -> OUT_OF_SYNC
    IDLE:
      0xFF -> IDLE
      0x7E -> START_FRAME
      * -> error, IDLE
    GET_FRAME:
      0x7E -> verify, queue, GET_FRAME
      0x7D -> GET_ESC
      * -> save, GET_FRAME
    GET_ESC:
      0x7E -> error, OUT_OF_SYNC
      0x7D -> error, OUT_OF_SYNC
      * -> save XOR 0x20, GET_FRAME
    '''

    def __init__(self, device):
        self.device = device
        self.state = IDLE
        self.statistics = create_statistics()
        self.frame = []
        self.completed_frames = deque()
        self.frame_error = False
        self.state_handler = {
            OUT_OF_SYNC: self.process_out_of_sync,
            IDLE: self.process_idle,
            GET_FRAME: self.process_get,
            GET_ESC: self.process_esc,
        }

    def _read(self):
        return self.device.read(1)

    def set_state(self, next_state):
        current_state = self.state

        if next_state == GET_FRAME:
            if current_state != GET_ESC:
                self.frame = []
                self.frame_error = False

        self.state = next_state

    def process_out_of_sync(self, c):
        if c == HDLC_FLAG:
            self.state = GET_FRAME

    def process_idle(self, c):
        if c == HDLC_IDLE:
            self.state = IDLE
        elif c == HDLC_FLAG:
            self.state = GET_FRAME
        else:
            self.statistics['unframed'] += 1

    def process_get(self, c):
        if c == HDLC_FLAG:
            if len(self.frame) == 0:
                self.statistics['empty'] = 1
            else:
                if self.verify_frame():
                    self.completed_frames.append(self.frame)
            self.set_state(GET_FRAME)
        elif c == HDLC_ESC:
            self.set_state(GET_ESC)
        else:
            self.frame.append(c)

    def process_esc(self, c):
        if c == HDLC_FLAG:
            self.statistics['escaped_flag'] += 1
            self.statistics['invalid'] += 1
            self.set_state(GET_FRAME)

        elif c == HDLC_ESC:
            self.statistics['double_escape'] += 1
            self.statistics['invalid'] += 1
            self.set_state(OUT_OF_SYNC)
        else:
            value = ord(c)
            decoded = value ^ HDLC_ESC_MOD
            self.frame.append(chr(decoded))
            self.set_state(GET_FRAME)

    def process_state(self, c):
        self.state_handler[self.state](c)

    def verify_frame(self):
        if len(self.frame) < 4:
            self.statistics['invalid'] += 1
            self.frame_error = True
            return False
        return True

    def get(self):
        self.frame_complete = False
        self.frame_error = False
        while True:
            c = self._read()

            if not c:
                self.statistics['timeout'] += 1
                return None

            # Add to byte count for every valid byte
            self.statistics['bytes'] += 1
            self.process_state(c)

            if self.completed_frames:
                return ''.join(self.completed_frames.popleft())
            if self.frame_error:
                return None
