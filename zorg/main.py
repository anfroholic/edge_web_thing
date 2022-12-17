import utime
from machine import Pin, CAN, ADC
import machine
import network
from neopixel import NeoPixel
import esp
esp.osdebug(None)
import uasyncio as asyncio
import struct
import os

import json


import gc
sd_contents = []
gc.collect()

import wlan

print('zorg board')
print('v1.7')
print('initializing')
this_id = 100
print(this_id)
broadcast_state = False
subscriptions = {}
connections = ''
sd_files = ''
port = 80

test_prog1 = [
[752, 690], # lcd button -> relay
[753, 691], # lcd button -> relay
[754, 692], # lcd button -> relay
[755, 693], # lcd button -> relay
[850, 794], # load cell -> lcd screen
[850, 491], # load cell -> servo
[1350, 792], # dpad pot -> lcd screen
[557, 492], # dpad pot -> servo
[558, 493], # dpad pot -> servo
[552, 994], # dpad up -> red stack
[553, 996], # dpad down -> green stack
[556, 999], # dpad push -> stack beeper
[941, 995], # stack latch -> self yellow
[550, 995],  # dpad_a -> stack yellow
[1251, 940],  # joy yellow -> stack latch
[1250, 996], # joy green -> green stack
[1253, 994], # joy red -> red stack
[1252, 999],
[1262, 495], # joy X -> servo
[1263, 496], # joy y -> servo
[1264, 497], # joy X -> servo
[1265, 498], # joy y -> servo
[1252, 1191], # joy blue -> mosfet 1
[1256, 1090], # joy up -> analog out1
[1258, 1091], # joy left -> analog out1
[1257, 1092], # joy down -> analog out2
[1259, 690], # joy right -> mosfet 1
[1254, 1191], # joy start -> analog out1
[1255, 691]
]




# Set up standard components
machine.freq(240000000)
hbt_led = Pin(15, Pin.OUT, value=0)

func_button = Pin(36, Pin.IN) # Has external pullup

neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
neo_status[0] = (0, 0, 0)
neo_status.write()

neo_bus_pin = Pin(27, Pin.OUT)
neo_bus = NeoPixel(neo_bus_pin, 1)
neo_bus[0] = (0, 0, 0)
neo_bus.write()


can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)

can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000)

buf = bytearray(8)
mess = [0, 0, 0, memoryview(buf)]


def mount_sd():
    global sd_files

    sd = machine.SDCard(slot=2)
    uos.mount(sd, "/sd")
    print('sd contents:')
    print(uos.listdir('/sd'))
    sd_files = ''.join(['<p>{}: {}</p>'.format(i, f) for i, f in enumerate(uos.listdir('/sd'))])


def file():
    with open('/sd/text.txt', 'r') as f:
        for line in f:
            yield line.strip()

def do_the_file():
    gen = file()
    for line in gen:
        print(json.loads(line))


class Button:
    def __init__(self, name, pin, pull_up, can_id):
        self.name = name
        print(self.name)
        #self.pin = pin
        self.pullup = pull_up
        self.state = None
        self.can_id = can_id + this_id
        if pull_up:
            self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        else:
            self.pin = Pin(pin, Pin.IN)
        self.state = self.pin.value()

    def check(self):
        global broadcast_state
        if self.state != self.pin.value():
            self.state = not self.state
            print('{} state: {} can_id: {}'.format(self.name, not self.state, self.can_id))
            if broadcast_state:
                can.send([not self.state], self.can_id)

class Analog:
    def __init__(self, name, pin, can_id):
        self.name = name
        print(self.name)
        self.state = None
        self.can_id = can_id + this_id
        self.pin = ADC(Pin(pin))
        self.pin.atten(ADC.ATTN_11DB)
        self.pin.width(ADC.WIDTH_12BIT)
        self.old = int(self.pin.read()/16)
    def check(self):
        self.state = int(self.pin.read()/16)
        global broadcast_state
        if abs(self.state - self.old) > 1:
            self.old = self.state
            print('{}: {} can_id: {}'.format(self.name, self.state, self.can_id))
            if broadcast_state:
                can.send([self.state], self.can_id)

class Operator:
    def __init__(self, name, can_id, broadcast_id):
        self.name = name
        self.latch = False
        self.can_id = can_id
        self.broadcast_id = this_id + broadcast_id
        print('{} initialized on can_id {}'.format(self.name, self.can_id))
        pass
    def _latch(self, switch):
        # global buf
        if switch == 1:
            self.latch = not self.latch
            if self.latch:
                buf[0] = 1
                can.send([1], self.broadcast_id)
            else:
                buf[0] = 0
                can.send([0], self.broadcast_id)
            print('latch: {} on id: {}'.format(buf[0], self.broadcast_id))
            if self.can_id + 1 + this_id in subscriptions:
                process(subscriptions[self.broadcast_id])
operator = Operator('_latch', 40, 41)

# a_button = Pin(32, Pin.IN, Pin.PULL_UP)
# b_button = Pin(32, Pin.IN, Pin.PULL_UP)
# c_button = Pin(32, Pin.IN, Pin.PULL_UP)
# d_button = Pin(32, Pin.IN, Pin.PULL_UP)
#
# # a_button = Button('a_button', 32, True, 50)
# # b_button = Button('b_button', 26, True, 51)
# # c_button = Button('c_button', 19, True, 52)
# # d_button = Button('d_button', 23, True, 53)
# # sd_detect = Pin(18, Pin.IN, Pin.PULL_UP)
# sd_detect = Button('sd_detect', 18, True, 54)
#
# led_a = Pin(33, Pin.OUT, value=0)
# led_b = Pin(25, Pin.OUT, value=0)
# led_c = Pin(21, Pin.OUT, value=0)
# led_d = Pin(22, Pin.OUT, value=0)

def mount_sd():
    global sd_contents
    if !sd_mounted:
        sd = machine.SDCard(slot=2)
        os.mount(sd, "/sd")  # mount

        sd_contents = os.listdir('/sd')    # list directory contents
        print(sd_contents)
    else:
        print('sd mounted already')


def list_sd():
    html = ''
    for file in sd_contents:
        this = f'<a href="/item/{file}"><button class="button button3">file</button></a>'.format(file)
        html.append(this)
    html.append('\n')
    return html

#network
lan = wlan.connect(neo_status)
my_ip = lan.ifconfig()[0]
neo_status[0] = (0, 10, 0)
neo_status.write()
utime.sleep_ms(250)
neo_status[0] = (0, 0, 0)
neo_status.write()


def web_page():
  # global connections

  html = """
<html>
    <head>
        <title>Evezor Web Interface</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
  h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
  border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  .button2{background-color: #4286f4;}.button3{background-color: #06876f;}.button4{background-color: #eb3440;}</style>
    </head>
    <body>
    <h1>Evezor Web Interface</h1>
    <p>Connections:</p> <strong>""" + connections + """</strong>
    <p>SD Contents:</p> <strong>""" + sd_files + """</strong>


    <p><a href="/led=off"><button class="button button2">neo off</button></a>
    <a href="/led=on"><button class="button">neo on</button></a>
    <a href="/?mount_sd"><button class="button button4">mount sd</button></a>
    </p>

    <p>
    <a href="/reset"><button class="button button3">reset</button></a>
    <a href="/light_show"><button class="button button3">light show</button></a>
    <a href="/broadcast"><button class="button button3">broadcast</button></a>
    <a href="/!broadcast"><button class="button button3">!broadcast</button></a>
    <a href="/demo_1"><button class="button button2">demo_1</button></a>
    </p>
    <br><br>
    <p><strong>Send CAN Message</strong></p>

    <form action="/can">
    <label for="send_arb">ARB:</label>
    <input type="text" id="send_arb" name="send_arb"><br><br>
    <label for="m0">m0:</label>
    <input type="text" id="m0" name="m0"><br>

    <label for="m1">m1:</label>
    <input type="text" id="m1" name="m1"><br>

    <label for="m2">m2:</label>
    <input type="text" id="m2" name="m2"><br>

    <label for="m3">m3:</label>
    <input type="text" id="m3" name="m3"><br>

    <label for="m4">m4:</label>
    <input type="text" id="m4" name="m4"><br>

    <label for="m5">m5:</label>
    <input type="text" id="m5" name="m5"><br>

    <label for="m6">m6:</label>
    <input type="text" id="m6" name="m6"><br>

    <label for="m7">m7:</label>
    <input type="text" id="m7" name="m7"><br>
    <input type="submit" value="Submit"></form>

    <br><br><p><strong>Create Subscriber</strong></p>

    <form action="/sub">
    <label for="sub_num">Broadcast ID:</label>
    <input type="text" id="sub_num" name="sub_num"><br><br>
    <label for="send_id">Subscriber ID:</label>
    <input type="text" id="send_id" name="send_id"><br><br>
    <input type="submit" value="Submit">
    </form>


    <br><br><p><strong>Upload Program</strong></p>

    <form action="/prog">
    <label for="prog">Program:</label>
    <input type="text" id="prog" name="prog"><br><br>
    <input type="submit" value="Submit">
    </form>

    </body></html>"""
  return html

async def get_can():
    while True:
        if can.any():
            can.recv(mess)
            print(str(mess[0]) + ', ' + str(buf[0]))
        await asyncio.sleep_ms(1)

async def buttons():
    pass
    # while True:
    #     # if not func_button.value():
    #     #     global broadcast_state
    #     #     print('function button pressed')
    #     #     broadcast_state = not broadcast_state
    #     #     broadcast(broadcast_state)
    #     #     await asyncio.sleep_ms(250)
    #     if not a_button.value():
    #             print('make demo 1')
    #             demo_1()
    #             await asyncio.sleep_ms(250)
    #     if not b_button.value():
    #             print('make demo 2')
    #     if not c_button.value():
    #             print('make demo 3')
    #     # a_button.check()
    #     # b_button.check()
    #     # c_button.check()
    #     # d_button.check()
    #     await asyncio.sleep_ms(150)

async def do_hbt():
    while True:
        hbt_led.value(1)
        await asyncio.sleep(.1)
        hbt_led.value(0)
        await asyncio.sleep(.9)

def send_can(request):
    end = request.find(' HTTP')
    action = request[13:end]
    action += '&'
    print(action)
    _mess = []
    for i in range(9):
        if action.find('&') - action.find('=') > 1:
            _mess.append(action[action.find('=')+1:action.find('&')])
            action = action[action.find('&')+1:]
    arb_id = int(_mess.pop(0))
    for i in range(len(_mess)): #convert to ints
        _mess[i] = int(_mess[i])
    print('sending')
    print(arb_id)
    print(_mess)
    can.send(_mess, arb_id)

def demo_1():
    global connections
    neo_status[0] = (0, 0, 20)
    neo_status.write()
    if connections == '':
        for sub in test_prog1:
            make_sub(sub[0], sub[1])
            utime.sleep_ms(25)
        # TODO: make the words show on lcd here
        utime.sleep_ms(25)
        can.send([1], 4) #  broadcast
        utime.sleep_ms(25)
        can.send([84, 69, 77, 80, 58, 32], 791) # TEMP:
        utime.sleep_ms(25)
        can.send([87, 69, 73, 71, 72, 84, 58, 32], 793) # WEIGHT:
    neo_status[0] = (0, 0, 0)
    neo_status.write()

def load_file(header):
    header = header.split('/')
    print(f'maybe we should load: {}'.format(header[1]))

def make_sub(sender, receiver):
    global connections
    connections += '<p>{}, {}</p>'.format(sender, receiver)
    board = int(receiver/100)*100
    print(board)
    receiver = receiver%100
    _mess = struct.pack('II', sender, receiver) # sender: receiver
    beer = []
    for i in range(len(_mess)):
        beer.append(int(_mess[i]))
    print('board: {}, reciever ID: {}, sender id: {}'.format(str(board), str(receiver), str(sender)))

    can.send(beer, board+49) # sub listener is on id 49

def parse_sub(request):
    end = request.find(' HTTP')
    action = request[13:end]
    print(action)
    sub = action.split('&')
    _sub = []
    for i in range(2):
        _sub.append(sub[i].split('=')[1])
        _sub[i] = int(_sub[i])
    make_sub(_sub[0],_sub[1])
    # board = int(_sub[1]/100)*100
    # print(board)
    # _sub[1] = _sub[1]%100
    # _mess = struct.pack('II', _sub[0], _sub[1]) # sender: receiver
    # beer = []
    # for i in range(len(_mess)):
    #     beer.append(int(_mess[i]))
    # print('board: {}, reciever ID: {}, sender id: {}'.format(str(board), str(_sub[1]), str(_sub[0])))
    # can.send(beer, board+49) # sub listener is on id 49

def parse_program(action):
    _prog = action.split('=')
    prog = _prog[1]
    while(len(prog) > 0):
        make_sub(int(prog[:4]), int(prog[4:8]))
        prog = prog[8:]

async def handle_client(reader, writer):
    request = (await reader.read(1024)).decode('ascii')
    # print(request)
    end = request.find(' HTTP')
    action = request[4:end]
    print(action)
    # process request
    if request.find('/can') == 4:
        send_can(request)
    if request.find('/sub') == 4:
        parse_sub(request)
    if request.find('/prog') == 4:
        parse_program(action)

    elif action == '/led=on':
        neo_status[0] = (0, 25, 0)
        neo_status.write()
    elif action == '/led=off':
        neo_status[0] = (0, 0, 0)
        neo_status.write()
    elif action == '/reset':
        # reset all boards
        global connections
        connections = ''
        can.send([1], 2)
    elif action == '/light_show':
        can.send([1], 1)
    elif action == '/broadcast':
        can.send([1], 4)
    elif action == '/!broadcast':
        can.send([0], 4)
    elif action == '/demo_1':
        demo_1()

    elif action.find('/item') == 0:
        load_file(action)

    elif action == '/?mount_sd':
        mount_sd()


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


def broadcast(state):
    if state:
        neo_status[0] = (0, 10, 0)
        neo_status.write()
    else:
        neo_status[0] = (0, 0, 0)
        neo_status.write()

def get():
    can.recv(mess)
    if mess[0] < 100 or (mess[0] >= this_id and mess[0] <= (this_id+99)):
        process(mess[0]%100)
    if mess[0] in subscriptions:
        process(subscriptions[mess[0]])
    # print(str(mess[0]) + ', ' + str(buf[0]))

def process(id):
    print(id)
    if id == 1:
        light_show()
    elif id == 2:
        machine.reset()
    elif id == 3:
        neo_status[0] = (buf[0], buf[1], buf[2])
        neo_status.write()
    elif id == 4:
        global broadcast_state
        broadcast_state = buf[0]
        broadcast(broadcast_state)
    elif id == 40:
        operator._latch(buf[0])
    elif id == 48:
        global subscriptions
        print('clearing subscriptions')
        subscriptions = {}
    elif id == 49:
        global subscriptions
        # add this to it's own sub list
        sub = struct.unpack('II', buf)
        subscriptions[sub[0]] = sub[1] # sender: receiver
        print(sub)

    elif id == 90:
        led_0.value(buf[0])
    elif id == 91:
        led_1.value(buf[0])
    elif id == 92:
        led_2.value(buf[0])
    elif id == 93:
        led_3.value(buf[0])

    else:
        print('unknown command')




async def main():
    asyncio.create_task(asyncio.start_server(handle_client, my_ip, port))
    asyncio.create_task(do_hbt())
    asyncio.create_task(buttons())
    asyncio.create_task(get_can())
    while True:
        await asyncio.sleep(5)


while True:
    asyncio.run(main())
