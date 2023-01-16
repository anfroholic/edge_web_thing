import config
from boards.utilities import *
import boards.iris as iris
import struct
import utime
from machine import Pin
import wifi_cred

print('loading cam')
cam_rst = Pin(27, Pin.OUT, Pin.PULL_UP)
grbl_uart = UartMgr(2, baudrate=115200, rx=14, tx=21)
cam_uart = UartMgr(1, baudrate=115200, rx=25, tx=26)

cam_rst.off()
utime.sleep_ms(100)
cam_rst.on()

class GRBL:
    def __init__(self, can, uart, hbt_int, debug=False, resets=False):
        self.can = can
        self.uart = uart

        self.connected = False
        self.state = 'idle'  # idle, run
        # self.states = {'idle': self.idle, 'run': run}
        self.axes = ['x', 'y', 'z', 'a']
        self.status = {
            'state': 'Sleep',
            'MPos': {'x': 0, 'y': 0, 'z': 0, 'a': 0},
            'limits': ''
        }
        self.offset = {
            'x': 0,
            'y': 0,
            'z': 0,
            'a': 0
        }

        self.queue = {}
        self.buf = []
        self.buf_loc = None

        # do heartbeat, poll grbl
        self.hbt_int = hbt_int
        self.next_hbt = utime.ticks_add(utime.ticks_ms(), self.hbt_int)

        self.debug = debug

    def chk(self):
        # do heartbeat, poll grbl
        if utime.ticks_diff(self.next_hbt, utime.ticks_ms()) <= 0:
            self.uart.write('?')
            self.next_hbt = utime.ticks_add(self.next_hbt, self.hbt_int)

        if self.uart.any():
            msg = self.uart.readline()
            if msg == '':
                return

            if msg[0] == '<':  # grbl info line
                msg = msg.strip('<>').split('|')
                self.status['state'] = msg[0]
                mpos = msg[1][5:].split(',')
                self.status['MPos']['x'] = float(mpos[0])
                self.status['MPos']['y'] = float(mpos[1])
                self.status['MPos']['z'] = float(mpos[2])
                # self.status['MPos']['a'] = float(mpos[3])
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
                        self.state == 'idle'
            else:
                print(msg)

    def status_str(self):
        return 'State: {}, x{}, y{}, z{}, a{}, {}'.format(self.status['state'],
                                                          round(self.status['MPos']['x'] - self.offset['x'], 3),
                                                          round(self.status['MPos']['y'] - self.offset['y'], 3),
                                                          round(self.status['MPos']['z'] - self.offset['z'], 3),
                                                          round(self.status['MPos']['a'] - self.offset['a'], 3),
                                                          self.status['limits'])

    def process(self, line):
        """ line is a grbl command convert it and send over uart """
        # print(line)
        grbl = ['move.linear', 'move.rapid', 'sleep']
        if line is None:
            pass

        elif line['cmd'] in grbl:
            """ process work offset """
            axis = ['x', 'y', 'z', 'a']
            for a in axis:
                if a in line:
                    line[a] = line[a] + self.offset[a]
            self.send_g(convert(**line))

        elif line['cmd'] in the_conversions:
            self.queue = dict(data=line['val'], arb_id=the_conversions[line['cmd']])
            self.send_g('G04 P0.1')

        else:
            print('must be comment or something?')
            print(line)
            self.process(self.get_next_cmd)

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


class Camera:
    def __init__(self, uart):
        self.uart = uart
    
    def chk(self):
        if self.uart.any():
            msg = self.uart.readline()
            print(msg)        
            if msg == 'SSID':
                self.uart.write(wifi_cred.cred[0])
            elif msg == 'PASSWORD':
                self.uart.write(wifi_cred.cred[1])
        



grbl = GRBL(can=iris.can, uart=grbl_uart, hbt_int=5000)
cam = Camera(cam_uart)



async def hw_chk():
    while True:
        grbl_uart.chk()
        cam_uart.chk()
        cam.chk()
        grbl.chk()
        
        await asyncio.sleep_ms(20)

    # -------------------------------------------------


#  if struct.unpack('?', m)[0]

this = {
    80: grbl.unlock,
    81: grbl.sleep,
    82: grbl.wake,
    83: lambda m: grbl.home('x') if bool(struct.unpack('b', m)[0]) else print('no homex'),
    84: lambda m: grbl.home('y') if bool(struct.unpack('b', m)[0]) else print('no homey'),
    85: lambda m: grbl.home('z') if bool(struct.unpack('b', m)[0]) else print('no homez'),
    86: grbl.movex,
    87: grbl.movey,
    88: grbl.movez
}
iris.things.update(this)
