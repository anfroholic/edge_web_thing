
import esp
esp.osdebug(None)
import gc
gc.collect()
from gcode_conversion import *  #asyncio does not seem to be able to make outside calls from within handle_client
import json
import uos
import utime
from machine import Pin, UART, CAN
import machine
import network
from neopixel import NeoPixel

import uasyncio as asyncio

print(machine.freq())
machine.freq(240000000)
print(machine.freq())

networks = {'Grammys_IoT':'AAGI96475', 'Herrmann': 'storage18', 'PumpingStationOne': 'ps1frocks'}
port = 80



# set up pins
hbt_led = Pin(5, Pin.OUT)
neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
neo_status[0] = (0, 0, 0)
neo_status.write()
func_button = Pin(36, Pin.IN) # Has external pullup
# sd_detect = Pin(10, Pin.IN, Pin.PULL_DOWN)

can_slp = Pin(19, Pin.OUT, value=0)
can_slp.value(0)
can = CAN(0, tx=18, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000)
print('GRBL board test')
print('V1.52')

#network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
neo_status[0] = (10, 0, 0)
aps = wlan.scan()
neo_status.write()

print(aps)

for i in range(len(aps)):
    station = aps[i][0].decode('ascii')
    if station in networks:
        print('connecting to ' + station + ', '+ networks[station])
        wlan.connect(station, networks[station])

neo_status[0] = (0, 0, 10)
neo_status.write()

while not wlan.isconnected():
    print(".", end = "")
    utime.sleep_ms(250)

print('Connection successful')
print(wlan.ifconfig())
neo_status[0] = (0, 10, 0)
neo_status.write()
my_ip = wlan.ifconfig()[0]



utime.sleep_ms(250)
uart1 = UART(1, baudrate=115200, tx=22, rx=23)

neo_status[0] = (0, 0, 0)
neo_status.write()



# uos.mount(sd, "/sd")
# print('sd contents:')
# print(uos.listdir('/sd'))
# utime.sleep(.25)

#set up other comms

gc.collect()



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
    <p>Connection State: <strong>""" + grbl.connection_state + """</strong></p>
    <p>State: <strong>""" + grbl.state + """</strong></p>
    <p>Running: <strong>""" + grbl.is_running + """</strong></p>


    <p><a href="/?led=off"><button class="button button2">neo off</button></a><a href="/?led=on"><button class="button">neo on</button></a>
    <a href="/?connect"><button class="button button2">unmount sd</button></a><a href="/?run"><button class="button button2">run</button></a></p>

    <p><a href="/?get_state"><button class="button button3">get_state</button></a><a href="/?unlock"><button class="button button3">unlock</button></a>
    <a href="/?sleep"><button class="button button3">sleep</button></a><a href="/?wake_up"><button class="button button3">wake up</button></a></p>

    <p><a href="/?homex"><button class="button button2">homex</button></a><a href="/?homey"><button class="button button2">homey</button></a>
    <a href="/?homexy"><button class="button button2">homexy</button></a><a href="/?homez"><button class="button button2">homez</button></a></p>

    <p><a href="/?mount_sd"><button class="button button3">mount sd</button></a><a href="/?nuke"><button class="button button4">NUKE</button></a><a href="/?get_line"><button class="button button3">get_line</button></a></p>

    <p><a href="/?ring_on"><button class="button button2">ring_on</button></a><a href="/?ring_off"><button class="button button2">ring_off</button></a>
    <a href="/?suck_on"><button class="button button2">suck_on</button></a><a href="/?suck_off"><button class="button button2">suck_off</button></a></p>

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

class GRBL:
    def __init__(self):
        self.connection_state = 'connected'
        self.is_running = 'False'
        self.sd_init = False
        self.sd_mounted = False

        self.to_parse = ''
        self.index = 0
        self.line = ''
        self.state = ''
        self.sd_state = 'unmounted'
        self.file_blurb = ''

        self.blurb_index = 0
        self.j_blurb = {}
        self.f = None
        self.queue = {}
        self.modal = ['move.linear', 'move.rapid', 'sleep']

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
        parsed['command'] = 'move.linear'
        parsed['feed'] = 2000
        return parsed

    def send(self, message):
        """
        send message to grbl board
        """
        if self.connection_state == 'connected':
            uart1.write(message + '\n')
        else:
            print(message)

    def get_line(self):
        """
        find line in text from grbl over uart
        """
        if self.to_parse != '':
            # print('trying to parse')
            self.index = self.to_parse.find('\r')
            # print(self.to_parse)
            # print(self.index)
            if len(self.to_parse) > 0: # check for empty line
                if self.index > 0:
                    self.line = self.to_parse[0:self.index]
                    self.to_parse = self.to_parse[(self.index + 2):]
                else:
                    self.to_parse = self.to_parse[2:]
                self.handler(self.line)

    def handler(self, line):
        """
        handler for incomming uart comms from grbl
        this also will send blurbs to grbl when running file from sd card
        """
        # print(line)
        if line == 'ok':
            if self.is_running == 'True':
                # print('todo: finish handler')
                self.get_next()
        elif line[0] == '<':
            print('update machine info')
            print(line)
            seg = line.split('|')
            grbl.state = seg[0][1:]
        elif line == '[MSG:Evezor]':
            print('got evezor message')
        else:
            print(line)
            # print('maybe need some other command thing')

    def get_next(self):
        """
        gets next line from sd card file
        """
        if self.queue:
            # if a message is in queue it probably means it's a can bus message.
            # a dwell has been sent in it's place last round and now it should send
            print('message in queue')
            print(self.queue)
            mess = [self.queue['val']]
            can.send(mess, the_conversions[self.queue['command']])
            self.queue = {}

        if len(self.file_blurb) < 200:
            self.file_blurb += self.f.read(100)

        self.blurb_index = self.file_blurb.find('\r')
        if len(self.file_blurb) > 0:
            if self.blurb_index > 0:
                self.j_blurb = json.loads(self.file_blurb[0:self.blurb_index])
                self.file_blurb = self.file_blurb[(self.blurb_index + 2):]
                # self.j_blurb = json.loads(self.blurb)
                # print(self.j_blurb)
                self.parse_message(self.j_blurb)
        else:
            print('must be the end of the file, maybe consider stop running')
            if self.queue:
                print('oops, guess there was one more command')
                self.get_next()
            else:
                self.is_running = 'False'
                print('closing file')
                self.f.close()
                # print('unmounting sd')
                # uos.umount('/sd')

    def file_opener(self, name):
        # TODO: make it so it doesn't break if file does not exist
        self.f = open(name, 'r')

    def parse_message(self, msg):
        """
        send message to converter or handle canbus requests
        """
        # print('parser')
        if msg['command'] in self.modal:
            # print('modal command')
            self.send(convert(**msg))
        elif 'command' in msg:
            # we need to wait until grbl is finished working on modal commands
            # and returns ok
            # print('pausing')
            self.queue = msg
            self.send('G4 P.01')
        else:
            print(msg)
            self.get_next()

    def can_send(self, mess, arb):
        can.send(mess, arb)


async def ck_buttons():
    while True:
        if not func_button.value():
            print('function button pressed')
            await asyncio.sleep_ms(250)
        await asyncio.sleep_ms(50)

async def do_hbt():
    while True:
        hbt_led.value(1)
        await asyncio.sleep(.1)
        hbt_led.value(0)
        await asyncio.sleep(.9)

async def handle_uart():
    while True:
        if uart1.any():
            grbl.to_parse += uart1.read(uart1.any()).decode('ascii')
            # print(grbl.to_parse)
        await asyncio.sleep_ms(5)

async def parse_grbl():
    while True:
        grbl.get_line()
        await asyncio.sleep_ms(5)

async def handle_client(reader, writer):
    request = (await reader.read(1024)).decode('ascii')
    # print(request)

    # find the action
    end = request.find(' HTTP')
    action = request[4:end]
    print(action)

    # process request
    if action.find('/move') == 0:
        parsed = grbl.parse_move(request)
        print(parsed)
        cmd = convert(**parsed)
        print(cmd)
        uart1.write(cmd + '\n')

    elif action == '/?led=on':
        print('turn led on')
        neo_status[0] = (0, 25, 0)
        neo_status.write()
    elif action == '/?led=off':
        print('turn led off')
        neo_status[0] = (0, 0, 0)
        neo_status.write()
    elif action == '/?connect':
        print('unmounting sd')
        uos.umount('/sd')
    elif action == '/?run':
        print('run')
        grbl.is_running = 'True'
        grbl.get_next()

    elif action == '/?get_state':
        # print('getting state')
        uart1.write('?')
    elif action == '/?unlock':
        print('unlocking')
        uart1.write('$X\n')
    elif action == '/?sleep':
        print('putting to sleep')
        uart1.write('$SLP\n')
    elif action == '/?wake_up':
        print('waking up grbl')
        uart1.write(b'\x18')
        uart1.write('\n')

    elif action == '/?homex':
        print('homing x')
        uart1.write('$HX\n')
    elif action == '/?homey':
        print('homing y')
        uart1.write('$HY\n')
    elif action == '/?homexy':
        print('homing xy')
        uart1.write('$HXY\n')
    elif action == '/?homez':
        print('homing z')
        uart1.write('$HZ\n')

    elif action == '/?mount_sd':

        print('mounting sd')
        if not grbl.sd_init:
            sd = machine.SDCard(slot=3)
        uos.mount(sd, "/sd")
        grbl.sd_mounted = True
        print('sd contents:')
        print(uos.listdir('/sd'))
    elif action == '/?nuke':
        print('nuking board')
        uos.remove('main.py')
        machine.reset()

    elif action == '/?ring_on':
        can.send([33,33,33], 397)
    elif action == '/?ring_off':
        can.send([0,0,0], 397)
    elif action == '/?suck_on':
        print('suction on')
        can.send([1], 399)
        print('message sent')
    elif action == '/?suck_off':
        can.send([0], 399)

    elif action.find('/file') == 0:
        print('opening file')
        if not grbl.sd_init:
            sd = machine.SDCard(slot=3)
        if not grbl.sd_mounted:
            uos.mount(sd, "/sd")
        fn = action.split('=')
        name = '/sd/' + fn[1]
        grbl.file_opener(name)

    elif action.find('/direct') == 0:
        fn = action.split('=')
        action = fn[1].replace('+', ' ')
        print('sending direct ' + action)
        action = action + '\n'
        uart1.write(action)

    elif action.find('/feeder') == 0:
        fn = action.split('=')
        print(fn)

    elif action == '/?get_line':
        print('getting next')
        grbl.get_next()
    else:
        print('unknown command')

    await writer.awrite(
        b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
    # with open(web_page(), 'rb') as response:
    #     while True:
    #         buf = response.read(1024)
    #         if len(buf):
    #             await writer.awrite(buf)
    #         if len(buf) < 1024:
    #             break
    await writer.awrite(web_page())
    await writer.aclose()
    return True


async def main():
    asyncio.create_task(asyncio.start_server(handle_client, my_ip, port))
    asyncio.create_task(do_hbt())
    asyncio.create_task(ck_buttons())
    asyncio.create_task(handle_uart())
    asyncio.create_task(parse_grbl())
    while True:
        await asyncio.sleep(5)

grbl = GRBL()
while True:
    asyncio.run(main())
