import json
import utime
from machine import Pin
import utime


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

axes = {
    'x': 'X',
    'y': 'Y',
    'z': 'Z',
    'a': 'A',
    'b': 'B',
    'c': 'C'
}


def convert(**line):
    """
    Convert json line into gcode
    """
    # print('converting')
    # print(line)
    if line['cmd'] == 'move.linear' or line['cmd'] == 'move.rapid':
        g_line = "G1 "
        for axis in axes:
            if axis in line:
                g_line += '{}{} '.format(axes[axis], round(float(line[axis]), 2))
        if 'feed' in line:
            g_line += 'F{}'.format(line['feed'])
        return g_line

    else:
        return "G4 P{}".format(line['val'])


class GRBL:
    def __init__(self, sd, can, uart, hbt_int, debug=False, resets=False):
        self.sd = sd
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
            'x': 10,
            'y': 20,
            'z': 30,
            'a': 0
        }

        self.queue = {}
        self.buf = []
        self.buf_loc = None

        # do heartbeat, poll grbl
        self.hbt_int = hbt_int
        self.next_hbt = utime.ticks_add(utime.ticks_ms(), self.hbt_int)

        self.debug = debug
        if resets:
            self.x_reset = Pin(14, Pin.OUT)
            self.y_reset = Pin(12, Pin.OUT)
            self.x_reset.on()
            self.y_reset.on()

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
                self.status['MPos']['a'] = float(mpos[3])
                self.status['limits'] = msg[3]
                print(self.status_str())

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

    def get_next_cmd(self) -> dict:
        """ get next command from sd or from buf """
        if self.buf_loc == 'sd':
            while True:
                line = self.sd.readline()
                if line is None:
                    print('end of file')
                    return None
                if line != '':
                    # print(line)
                    return json.loads(line)
        else:
            line = self.buf.pop(0)
            if self.debug:
                print(line)
            if line is None:
                    print('end of file')
                    return None
            return line

    def run(self, *, buf_loc='buf'):
        """ start running from pre opened sd file or from preloaded self.buf """
        self.buf_loc = buf_loc
        self.state = 'run'
        if buf_loc == 'sd':
            while True:
                line = self.get_next_cmd()
                if 'cmd' in line:
                    self.process(line)
                    self.state = 'run'
                    break
                if self.debug:
                    print(line)
        else:
            self.process(self.get_next_cmd())

    def load_buf(self, program):
        self.buf = program
        if self.debug:
            print(self.buf)

    def unlock(self):
        self.send_g('$X')

    def sleep(self):
        self.send_g('$SLP')

    def wake(self):
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

    def reset_axis(self, axis):
        axes = {'x': self.x_reset, 'y': self.y_reset}
        axes[axis].off()
        utime.sleep_ms(1)
        axes[axis].on()

    def parse_move(self, request):
        """
        parse move that came from web socket
        """
        end = request.find(' HTTP')
        action = request[14:end]
        action += '&'
        # print('parsing request')
        # print(action)
        axes = ['x', 'y', 'z', 'a']
        parsed = {}
        for axis in axes:
            index = action.find('&')
            if action[2: index] != '':
                parsed[axis] = action[2: index]
            action = action[(index + 1):]
        # print(parsed)
        parsed['cmd'] = 'move.linear'
        print(parsed)
        for a in axes:
            if a in parsed:
                parsed[a] = int(parsed[a]) + self.offset[a]
        parsed['feed'] = 2000
        self.send_g(convert(**parsed))

    def set_offset(self, request: str) -> None:
        """ parse offsets from websocket """
        action = request[request.find('?') + 1: request.find(' HTTP')]
        action = [a.split('=') for a in action.split('&')]
        for a, v in action:
            if v != '':
                self.offset[a] = float(v)


    def web_buts(self):
        return {
            '/?get_state': lambda: self.uart.write('?'),
            '/?unlock': lambda: self.unlock(),
            '/?sleep': lambda: self.sleep(),
            '/?wake_up': lambda: self.wake(),
            '/?run': lambda: self.run(buf_loc='sd'),
            '/?homex': lambda: self.home('x'),
            '/?homey': lambda: self.home('y'),
            '/?homez': lambda: self.home('z'),
            '/?homea': lambda: self.home('a'),
            '/?homeb': lambda: self.home('b'),
            '/?homec': lambda: self.home('c'),
            '/?ring_on': lambda: self.can.send([33,33,33], 397),
            '/?ring_off': lambda: self.can.send([0,0,0], 397),
            '/?suck_on': lambda: self.can.send([1], 399),
            '/?suck_off': lambda: self.can.send([0], 399),
            '/?spindle_on': lambda: self.can.send([1], 1492),
            '/?spindle_off': lambda: self.can.send([0], 1492),
            '/?vise_open': lambda: self.can.send([1], 1196),
            '/?vise_close': lambda: self.can.send([0], 1196),
            '/?coolant_on': lambda: self.can.send([1], 1195),
            '/?coolant_off': lambda: self.can.send([0], 1195),
            '/?reset_theta': lambda: self.grbl.reset_axis('x'),
            '/?reset_phi': lambda: self.grbl.reset_axis('y'),
            '/?run_script': lambda: self.run()
        }
    def web_page(self):


        html = """
<html>
    <head>
        <title>Evezor Robotic Arm</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
  h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
  border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  .button2{background-color: #4286f4;}.button3{background-color: #06876f;}.button4{background-color: #E1341E;}</style>
    </head>
    <body>
    <h1>Evezor Robotic Arm</h1>
    <p>State: """ + self.status_str() + """</p>

    <p><a href="/home"><button class="button button2">home</button></a>
    <a href="/led=off"><button class="button button2">neo off</button></a><a href="/led=on"><button class="button">neo on</button></a>
    <a href="/connect"><button class="button button2">unmount sd</button></a><a href="/?run"><button class="button button2">run</button></a></p>

    <p><a href="/?get_state"><button class="button button3">get_state</button></a><a href="/?unlock"><button class="button button3">unlock</button></a>
    <a href="/?sleep"><button class="button button3">sleep</button></a><a href="/?wake_up"><button class="button button3">wake up</button></a></p>

    <p><a href="/?homex"><button class="button button2">homex</button></a><a href="/?homey"><button class="button button2">homey</button></a>
    <a href="/?homez"><button class="button button2">homez</button></a>
    <a href="/?homea"><button class="button button2">homea</button></a><a href="/?homeb"><button class="button button2">homeb</button></a><a href="/?homec"><button class="button button2">homec</button></a></p>

    <p><a href="/?ring_on"><button class="button button2">ring_on</button></a><a href="/?ring_off"><button class="button button2">ring_off</button></a>
    <a href="/?suck_on"><button class="button button2">suck_on</button></a><a href="/?suck_off"><button class="button button2">suck_off</button></a></p>

    <p><a href="/?spindle_on"><button class="button button2">spindle_on</button></a><a href="/?spindle_off"><button class="button button2">spindle_off</button></a>
    <a href="/?vise_open"><button class="button button2">vise_open</button></a><a href="/?vise_close"><button class="button button2">vise_close</button></a></p>

    <p><a href="/?coolant_on"><button class="button button2">coolant_on</button></a><a href="/?coolant_off"><button class="button button2">coolant_off</button></a><a href="/?run_export"><button class="button button2">run_export.txt</button></a></p>
    <p><a href="/?reset_theta"><button class="button button3">reset_theta</button></a><a href="/?reset_phi"><button class="button button3">reset_phi</button></a><a href="/?run_script"><button class="button button2">runscript</button></a></p>

    <br><br>
    <p><strong>Move Machine</strong></p>

    <form action="/move.php">
    <label for="send_x">X:</label>
    <input type="text" id="x" name="x"><br><br>
    <label for="send_y">Y:</label>
    <input type="text" id="y" name="y"><br><br>
    <label for="send_z">Z:</label>
    <input type="text" id="z" name="z"><br><br>
    <label for="send_a">A:</label>
    <input type="text" id="a" name="a"><br><br>
    <input type="submit" value="Submit">
    </form>

    <p><strong>file</strong></p>
    <form action="/file.php">
    <label for="file">file:</label>
    <input type="text" id="file" name="file"><br><br>
    <input type="submit" value="Submit">
    </form>

    <p><strong>direct</strong></p>
    <form action="/direct.php">
    <label for="direct">direct:</label>
    <input type="text" id="direct" name="direct"><br><br>
    <input type="submit" value="Submit">
    </form>

    <p><strong>feeder</strong></p>
    <form action="/feeder.php">
    <label for="feeder">feeder:</label>
    <input type="text" id="feeder" name="feeder"><br><br>
    <input type="submit" value="Submit">
    </form>

    <p><strong>set offset</strong></p>
    <form action="/offset.php">
    <label for="send_x">X:</label>
    <input type="text" id="x" name="x"><br><br>
    <label for="send_y">Y:</label>
    <input type="text" id="y" name="y"><br><br>
    <label for="send_z">Z:</label>
    <input type="text" id="z" name="z"><br><br>
    <label for="send_a">A:</label>
    <input type="text" id="a" name="a"><br><br>
    <input type="submit" value="Submit">
    </form>

    </body></html>"""
        return html
