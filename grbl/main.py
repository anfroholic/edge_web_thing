
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


ssid = 'Grammys_IoT'
password = 'AAGI96475'
port = 80
loop = asyncio.get_event_loop()


# set up pins
hbt_led = Pin(5, Pin.OUT)
neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
func_button = Pin(36, Pin.IN) # Has external pullup
# sd_detect = Pin(10, Pin.IN, Pin.PULL_DOWN)

print('GRBL board test')
print('V1.5')
#network
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

neo_status[0] = (10, 0, 0)
neo_status.write()
while not station.isconnected():
    print(".", end = "")
    utime.sleep_ms(250)

print('Connection successful')
print(station.ifconfig())
my_ip = station.ifconfig()[0]
neo_status[0] = (0, 10, 0)
neo_status.write()
utime.sleep_ms(250)
neo_status[0] = (0, 0, 10)
neo_status.write()
utime.sleep(.25)




# uos.mount(sd, "/sd")
# print('sd contents:')
# print(uos.listdir('/sd'))
# utime.sleep(.25)
neo_status[0] = (0, 0, 0)
neo_status.write()

#set up other comms
uart1 = UART(1, baudrate=115200, tx=22, rx=23)


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

    <p><a href="/?led=off"><button class="button button2">neo off</button></a>          <a href="/?led=on"><button class="button">neo on</button></a><a href="/?connect"><button class="button button2">connect</button></a></p>

    <p><a href="/?get_state"><button class="button button3">get_state</button></a><a href="/?unlock"><button class="button button3">unlock</button></a>
    <a href="/?sleep"><button class="button button3">sleep</button></a><a href="/?wake_up"><button class="button button3">wake up</button></a></p>

    <p><a href="/?homex"><button class="button button2">homex</button></a><a href="/?homey"><button class="button button2">homey</button></a>
    <a href="/?homexy"><button class="button button2">homexy</button></a><a href="/?homez"><button class="button button2">homez</button></a></p>

    <p><a href="/?mount_sd"><button class="button button3">mount sd</button></a><a href="/?nuke"><button class="button button4">NUKE</button></a><a href="/?get_line"><button class="button button3">get_line</button></a></p>

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
    </body></html>"""
  return html

class GRBL:
    def __init__(self):
        self.connection_state = 'not connected'
        self.to_parse = ''
        self.index = 0
        self.line = ''
        self.is_running = False
        self.state = ''
        self.sd_state = 'unmounted'
        self.file_blurb = ''
        self.blurb_index = 0
        self.blurb = ''
        self.f = None

    def parse_move(self, request):
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
        """
        print(line)
        if line == 'ok':
            if self.is_running:
                print('todo: finish handler')
        elif line[0] == '<':
            print('update machine info')
            seg = line.split('|')
            grbl.state = seg[0][1:]
        else:
            # print('maybe need some other command thing')
            pass

    def get_next(self):
        """
        gets next line from sd card file
        """
        if len(self.file_blurb) < 200:
            self.file_blurb += self.f.read(100)
        self.blurb_index = self.file_blurb.find('\r')
        if len(self.file_blurb) > 0:
            if self.blurb_index > 0:
                self.blurb = self.file_blurb[0:self.blurb_index]
                self.file_blurb = self.file_blurb[(self.blurb_index + 2):]
                print(self.blurb)

    def file_opener(self, name):
        self.f = open(name, 'r')



async def buttons():
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
    end = request.find(' HTTP')
    action = request[4:end]
    print(action)
    # process request
    if action.find('/move') == 4:
        parsed = parse_move(request)
        print(convert(**parsed))

    elif action == '/?led=on':
        print('turn led on')
        neo_status[0] = (0, 25, 0)
        neo_status.write()
    elif action == '/?led=off':
        print('turn led off')
        neo_status[0] = (0, 0, 0)
        neo_status.write()
    elif action == '/?connect':
        print('connecting')
        grbl.connection_state = 'connected'
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
        sd = machine.SDCard(slot=3)
        print('mounting sd')
        uos.mount(sd, "/sd")
        print('sd contents:')
        print(uos.listdir('/sd'))
    elif action == '/?nuke':
        print('nuking board')
        uos.remove('main.py')
        machine.reset()
    elif action.find('/file') == 0:
        print('opening file')
        fn = action.split('=')
        name = '/sd/' + fn[1]
        grbl.file_opener(name)

    elif action == '/?get_line':
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
    asyncio.create_task(buttons())
    asyncio.create_task(handle_uart())
    asyncio.create_task(parse_grbl())
    while True:
        await asyncio.sleep(5)

grbl = GRBL()
while True:
    asyncio.run(main())
