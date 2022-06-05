import json
import utime


def web_page():


  html = """
<html>
    <head>
        <title>Evezor Web Interface</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
  h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
  border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  .button2{background-color: #4286f4;}.button3{background-color: #06876f;}.button4{background-color: #E1341E;}</style>
    </head>
    <body>
    <h1>Evezor Web Interface</h1>



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
    </body></html>"""
  return html

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
    def __init__(self, sd, can, uart, hbt_int):
        self.sd = sd
        self.can = can
        self.uart = uart

        self.connected = False
        self.state = 'idle'  # idle, run
        # self.states = {'idle': self.idle, 'run': run}

        self.queue = {}

        self.hbt_int = hbt_int
        self.next_hbt = utime.ticks_add(utime.ticks_ms(), self.hbt_int)

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
                print(msg)

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

    def process(self, line):
        # print(line)
        grbl = ['move.linear', 'move.rapid', 'sleep']
        if line is None:
            pass
        
        elif line['cmd'] in grbl:
            self.send_g(convert(**line))

        elif line['cmd'] in the_conversions:
            self.queue = dict(data=line['val'], arb_id=the_conversions[line['cmd']])
            self.send_g('G04 P0.1')

        else:
            print('must be comment or something?')
            print(line)
            self.process(self.get_next_cmd)

    def get_next_cmd(self):
        while True:
            line = self.sd.readline()
            if line is None:
                print('end of file')
                return None
            if line != '':
                # print(line)
                return json.loads(line)
            

    def run(self):
        while True:
            line = self.get_next_cmd()
            if 'cmd' in line:
                self.process(line)
                self.state = 'run'
                break
            print(line)
            
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
