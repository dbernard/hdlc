from collections import deque

# Taken from RFC 1662.
# The FCS-32 generator polynomial: x**0 + x**1 + x**2 + x**4 + x**5
#                      + x**7 + x**8 + x**10 + x**11 + x**12 + x**16
#                      + x**22 + x**23 + x**26 + x**32.

fcs32_table = [
    0x00000000, 0x77073096, 0xee0e612c, 0x990951ba,
    0x076dc419, 0x706af48f, 0xe963a535, 0x9e6495a3,
    0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988,
    0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91,
    0x1db71064, 0x6ab020f2, 0xf3b97148, 0x84be41de,
    0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
    0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec,
    0x14015c4f, 0x63066cd9, 0xfa0f3d63, 0x8d080df5,
    0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172,
    0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b,
    0x35b5a8fa, 0x42b2986c, 0xdbbbc9d6, 0xacbcf940,
    0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
    0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116,
    0x21b4f4b5, 0x56b3c423, 0xcfba9599, 0xb8bda50f,
    0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924,
    0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d,
    0x76dc4190, 0x01db7106, 0x98d220bc, 0xefd5102a,
    0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
    0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818,
    0x7f6a0dbb, 0x086d3d2d, 0x91646c97, 0xe6635c01,
    0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e,
    0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457,
    0x65b0d9c6, 0x12b7e950, 0x8bbeb8ea, 0xfcb9887c,
    0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
    0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2,
    0x4adfa541, 0x3dd895d7, 0xa4d1c46d, 0xd3d6f4fb,
    0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0,
    0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9,
    0x5005713c, 0x270241aa, 0xbe0b1010, 0xc90c2086,
    0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
    0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4,
    0x59b33d17, 0x2eb40d81, 0xb7bd5c3b, 0xc0ba6cad,
    0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a,
    0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683,
    0xe3630b12, 0x94643b84, 0x0d6d6a3e, 0x7a6a5aa8,
    0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
    0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe,
    0xf762575d, 0x806567cb, 0x196c3671, 0x6e6b06e7,
    0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc,
    0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5,
    0xd6d6a3e8, 0xa1d1937e, 0x38d8c2c4, 0x4fdff252,
    0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
    0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60,
    0xdf60efc3, 0xa867df55, 0x316e8eef, 0x4669be79,
    0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236,
    0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f,
    0xc5ba3bbe, 0xb2bd0b28, 0x2bb45a92, 0x5cb36a04,
    0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
    0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a,
    0x9c0906a9, 0xeb0e363f, 0x72076785, 0x05005713,
    0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38,
    0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21,
    0x86d3d2d4, 0xf1d4e242, 0x68ddb3f8, 0x1fda836e,
    0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
    0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c,
    0x8f659eff, 0xf862ae69, 0x616bffd3, 0x166ccf45,
    0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2,
    0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db,
    0xaed16a4a, 0xd9d65adc, 0x40df0b66, 0x37d83bf0,
    0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
    0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6,
    0xbad03605, 0xcdd70693, 0x54de5729, 0x23d967bf,
    0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94,
    0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d,
]


FCS32_GOOD_FINAL=0xdebb20e3


def compute_fcs32(data, fcs=None):
    if fcs is None:
        fcs = 0xFFFFFFFF

    for i in range(len(data)):
       fcs = (fcs >> 8) ^ fcs32_table[(fcs ^ ord(data[i])) & 0xff]

    return fcs


def append_fcs32(data):
    # Note: the complement of the FCS is appended to the data, LSB first.
    # ~0xB5E84EA9 = 0x4A17B156
    fcs = compute_fcs32(data) ^ 0xFFFFFFFF
    for i in xrange(4):
        data += chr(fcs & 0xFF)
        fcs >>= 8
    return data


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
        'fcs': 0,
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
        self.esc_chars = [HDLC_FLAG, HDLC_ESC]
        self.state_handler = {
            OUT_OF_SYNC : self.process_out_of_sync,
            IDLE: self.process_idle,
            GET_FRAME: self.process_get,
            GET_ESC: self.process_esc,
        }

    def _read(self):
        '''
        Read incoming bytes from the HDLC device.
        '''
        return self.device.read(1)

    def set_state(self, next_state):
        '''
        Set the HDLC state flag to the given state to be processed.
        '''
        current_state = self.state

        if next_state == GET_FRAME:
            if current_state != GET_ESC:
                del self.frame[:]

        self.state = next_state

    def process_out_of_sync(self, c):
        '''
        Handle an out of sync HDLC state.
        '''
        if c == HDLC_FLAG:
            self.state = GET_FRAME

    def _write(self, data):
        '''
        Write data to the HDLC connected device.
        '''
        self.device.write(data)

    def process_idle(self, c):
        '''
        Handle an HDLC_IDLE state.
        '''
        if c == HDLC_IDLE:
            self.state = IDLE
        elif c == HDLC_FLAG:
            self.state = GET_FRAME
        else:
            self.statistics['unframed'] += 1

    def process_get(self, c):
        '''
        Compile incoming bytes into usable data.

        Through this process, drop the HDLC flags off of the beginning and end
        of the data, as well as the FCS value (after verifying it). If a bad
        frame is received, replace it with a None object.
        '''
        if c == HDLC_FLAG:
            if len(self.frame) == 0:
                self.statistics['empty'] = 1
            else:
                frame = '' .join(self.frame)
                if self.verify_frame(frame):
                    # Drop the FCS off of the queued frame.
                    self.completed_frames.append(frame[:-4])
                else:
                    # Bad frame.  Tack in a None object to indicate this.
                    self.completed_frames.append(None)

            self.set_state(GET_FRAME)

        elif c == HDLC_ESC:
            self.set_state(GET_ESC)

        else:
            self.frame.append(c)

    def process_esc(self, c):
        '''
        When an escape character is received, decode or handle it accordingly
        and reset the state (OUT_OF_SYNC for a double escape, GET_FRAME
        otherwise).
        '''
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
        '''
        Call the appropriate function based on received data.
        '''
        self.state_handler[self.state](c)

    def verify_frame(self, frame):
        '''
        Verify appropriate frame length and FCS value.
        '''
        if len(frame) < 4:
            self.statistics['invalid'] += 1
            return False

        fcs = compute_fcs32(frame)
        if fcs != FCS32_GOOD_FINAL:
            self.statistics['fcs'] += 1
            return False

        return True

    def get(self):
        '''
        Retrieve data and return a frame from the HDLC.

        Checks for incoming data. Based on received data, process the current
        state of the HDLC and build data accordingly. If we do not detect any
        incoming data and timeout, return None. If completed frames are
        detected, return them (FIFO).
        '''
        while True:
            c = self._read()

            if not c:
                self.statistics['timeout'] += 1
                return None

            # Add to byte count for every valid byte
            self.statistics['bytes'] += 1
            self.process_state(c)

            if self.completed_frames:
                return self.completed_frames.popleft()

    def send(self, channel, control, data):
        '''
        Build and send a data frame through the HDLC.

        Data frames consist of an HDLC_FLAG followed by the channel, the
        control, the data, the FCS (all escaped), and ending with an HDLC_FLAG.
        '''
        data = append_fcs32(chr(channel) + chr(control) + data)

        coded = []
        for character in data:
            # XOR any esc pieces of the data with HDLC_ESC_MOD
            if character in self.esc_chars:
                character = HDLC_ESC + (character ^ HDLC_ESC_MOD)
            coded.append(character) 

        coded = ''.join(coded)

        frame = HDLC_FLAG + coded + HDLC_FLAG

        self._write(frame)

