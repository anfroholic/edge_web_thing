import utime
import boards.iris as iris
import struct
import json

the_conversions = {
    'suction': 399,
    'feed.feeder': 398,
    'ring_light': 397,
    'spindle.on': 1181,
    'spindle.off': 1180,
    'vise': 1196,
    'coolant': 1195,
    'spindle': 1492
}


class Loader:
    """
    returns generator objects for CNC
    """

    def __init__(self, **k):
        pass

    def __call__(self, item):
        if type(item) is str:
            return self._open(item)
        elif type(item) is list:
            return self._load(item)
        elif this.__class__.__name__ == 'generator':
            return item

    @staticmethod
    def _load(_list):
        yield from _list

    @staticmethod
    def _open(file):
        with open(file, 'r') as f:
            for line in f:
                yield json.loads(line.strip())

    # -------------------------------------------------

class GRBL:
    def __init__(self, can, uart, hbt_int, axes, debug=False, resets=False):
        self.can = can
        self.uart = uart

        self.connected = False
        self.state = 'idle'  # idle, run
        # self.states = {'idle': self.idle, 'run': run}
        self.axes = axes
        self.status = {
            'state': 'Sleep',
            'MPos': {axis: 0 for axis in self.axes},
            'limits': ''
        }
        self.offset = {axis: 0 for axis in self.axes}

        self.positions = {'x':0, 'y':0, 'z':0}
        self.queue = {}
        self.buf = []
        self.buf_loc = None

        # do heartbeat, poll grbl
        self.hbt_int = hbt_int
        self.next_hbt = utime.ticks_add(utime.ticks_ms(), self.hbt_int)

        self.debug = debug
        self.script = None
        self.loader = Loader()

    # -------------------------------------------------
    
    def chk(self):
        # do heartbeat, poll grbl
        if utime.ticks_diff(self.next_hbt, utime.ticks_ms()) <= 0:
            self.uart.write('?')
            self.next_hbt = utime.ticks_add(self.next_hbt, self.hbt_int)

        if self.uart.any():
            msg = self.uart.readline()
            if msg == '':
                return

            if msg[0] == '<': # grbl info line
                msg = msg.strip('<>').split('|')
                self.status['state'] = msg[0]
                mpos = msg[1][5:].split(',')
                self.status['MPos']['x'] = float(mpos[0])
                self.status['MPos']['y'] = float(mpos[1])
                self.status['MPos']['z'] = float(mpos[2])
                # self.status['MPos']['a'] = float(mpos[3])
                self.positions['x'] = self.status['MPos']['x'] - self.offset['x']
                self.positions['y'] = self.status['MPos']['y'] - self.offset['y']
                self.positions['z'] = self.status['MPos']['z'] - self.offset['z']
                self.status['limits'] = msg[3]
                print(self.status_str())
                iris.stater(self.status['state'], 50)

            elif msg == 'ok':
                if self.state == 'run':
                    if self.queue != {}:
                        self.send_c(**self.queue)
                        self.queue = {}


                    new_line = self.get_next_cmd()
                    if new_line is not None:
                        self.process(new_line)
                    else:
                        print('file complete')
                        self.state = 'idle'
            else:
                print(msg)

    # -------------------------------------------------
    
    def status_str(self):
        return 'State: {}, x{}, y{}, z{}, {}'.format(self.status['state'],
                                                          self.positions['x'],
                                                          self.positions['y'],
                                                          self.positions['z'],
                                                          self.status['limits'])

    # -------------------------------------------------
    
    def process(self, line):
        """ line is a grbl command convert it and send over uart """
        # print(line)
        grbl = ['move.linear', 'move.rapid', 'sleep']
        if line is None:
            pass

        elif line['cmd'] in grbl:
            """ process work offset """
            for a in self.axes:
                if a in line:
                    line[a] = line[a] + self.offset[a]
            self.send_g(self.convert(**line))

        elif line['cmd'] in the_conversions:
            self.queue = dict(data=line['val'], arb_id=the_conversions[line['cmd']])
            self.send_g('G04 P0.1')

        else:
            print('must be comment or something?')
            print(line)
            self.process(self.get_next_cmd())

    def convert(self, **line):
        """
        Convert json line into gcode
        """
        # print('converting')
        # print(line)
        if line['cmd'] == 'move.linear' or line['cmd'] == 'move.rapid':
            g_line = "G1 "
            for axis in self.axes:
                if axis in line:
                    g_line += '{}{} '.format(axis.upper(), round(float(line[axis]), 2))
            if 'feed' in line:
                g_line += 'F{}'.format(line['feed'])
            return g_line

        else:
            return "G4 P{}".format(line['val'])
    
    def get_next_cmd(self):
        try:
            return next(self.script)
        except StopIteration:
            return None

    # -------------------------------------------------
    
    def load_buf(self, program):
        self.buf = program
        if self.debug:
            print(self.buf)

    def unlock(self, *args):
        self.send_g('$X')

    def sleep(self, *args):
        self.send_g('$SLP')

    def wake(self, *args):
        self.uart.write(b'\x18')
        self.uart.write('\n')

    def home(self, axis):
        self.send_g('$H{}'.format(axis.upper()))

    def send_g(self, cmd):
        print(cmd)
        self.uart.write(cmd + '\n')

    def send_c(self, **cmd):
        print(cmd)
        # self.can.send(**cmd)

    def movex(self, msg):
        pos = struct.unpack('f', msg)[0]
        self.send_g(f'G1 X{pos} F2000')

    def movey(self, msg):
        pos = struct.unpack('f', msg)[0]
        self.send_g(f'G1 Y{pos} F2000')

    def movez(self, msg):
        pos = struct.unpack('f', msg)[0]
        self.send_g(f'G1 Z{pos} F2000')

    def move(self, positions: dict):
        line = 'G1 '
        for axis in self.axes:
            if axis in positions:
                dif = self.positions[axis] - positions[axis]
                raw = self.positions[axis] + self.offset[axis]
                # print('dif:', dif, 'raw:', raw)
                line += f'{axis.upper()}{raw - dif} '
        if 'feed' in positions:
            line += f'F{positions["feed"]}'
        else:
            line += 'F500'
        # print(line)
        self.send_g(line)
        
    def set_hbt(self, msg):
        """
        set inerval for '?' status check to grbl
        """
        self.hbt_int = struct.unpack('B', msg)[0] * 100

    def load_script(self, script):
        print('loading', script)
        self.script = self.loader(script)
        self.state = 'run'
        self.process(self.get_next_cmd())


