class State(object):
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return self._name

    def __repr__(self):
        return '<State {0}>'.format(self._name)

    def __hash__(self):
        return hash(repr(self))


IDLE = State("Idle")
START_FRAME = State("Start Frame")
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

    IDLE:
      0xFF -> IDLE
      0x7E -> START_FRAME
      * -> error, IDLE
    START_FRAME
      0x7E -> EMPTY
      START_FRAME
      * -> GET_FRAME
    GET_FRAME
      0x7E -> verify, START_FRAME
      0x7D -> GET_ESC
      * -> save, GET_FRAME
    GET_ESC
      0x7E -> error, START_FRAME
      0x7D -> error, IDLE
      * -> save XOR 0x20, GET_FRAME
    '''

    def __init__(self, device):
        self.device = device
        self.state = IDLE
        self.statistics = create_statistics()
        self.frame = []
        self.frame_complete = False
        self.frame_error = False
        self.state_handler = {
            IDLE: self.process_idle,
            START_FRAME: self.process_start,
            GET_FRAME: self.process_get,
            GET_ESC: self.process_esc,
        }

    def _read(self):
        return self.device.read(1)

    def process_idle(self, c):
        if c == HDLC_IDLE:
            self.state = IDLE
        elif c == HDLC_FLAG:
            self.state = START_FRAME
        else:
            self.statistics['unframed'] += 1

    def process_start(self, c):
        if c == HDLC_FLAG:
            self.statistics['empty'] += 1
        elif c == HDLC_IDLE:
            self.state = IDLE
        elif c == HDLC_ESC:
            self.state = GET_ESC
            self.frame = []
        else:
            self.state = GET_FRAME
            self.frame = [c]

    def process_get(self, c):
        if c == HDLC_FLAG:
            self.verify_frame()
        elif c == HDLC_ESC:
            self.state = GET_ESC
        else:
            self.frame.append(c)

    def process_esc(self, c):
        if c == HDLC_FLAG:
            self.statistics['escaped_flag'] += 1
            self.state = START_FRAME
        elif c == HDLC_ESC:
            self.statistics['double_escape'] += 1
            self.state = IDLE
        else:
            value = ord(c)
            decoded = value ^ HDLC_ESC_MOD
            self.frame.append(chr(decoded))
            self.state = GET_FRAME

    def process_state(self, c):
        self.state_handler[self.state](c)

    def verify_frame(self):
        if len(self.frame) < 4:
            self.statistics['invalid'] += 1
            self.frame_error = True
            return
        self.frame_complete = True

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
            if self.frame_complete:
                return ''.join(self.frame)
            if self.frame_error:
                return None
