
"""
version: 0.12
7/29/22
"""

from machine import Pin, ADC, CAN, UART, PWM
import utime
from neopixel import NeoPixel
import uos
import machine
import uasyncio as asyncio
import math
import config
import struct
import boards.iris
from boards.umqtt.robust import MQTTClient

this_id = config.config['id']


class UartMgr:
    def __init__(self, bus, *, tx, rx, baudrate):
        self.uart = UART(bus, tx=tx, rx=rx, baudrate=baudrate)
        self.buf = ''
        self.lines = []

    def chk(self):
        if self.uart.any():
            self.buf += self.uart.read().decode('utf8')

            while True:
                # get lines
                index = self.buf.find('\r\n')
                if index == -1:
                    break

                self.lines.append(self.buf[:index])
                self.buf = self.buf[(index + 2):]

    def write(self, msg):
        self.uart.write(msg)


    def any(self):
        if self.lines:
            return True
        return False

    def readline(self):
        return self.lines.pop(0)
    
    # -------------------------------------------------

class CanMgr:
    def __init__(self, bus, *, tx, rx, extframe, mode, baudrate, slp_pin):
        self.can = CAN(bus, tx=tx, rx=rx, extframe=extframe, mode=mode, baudrate=baudrate, rx_queue=25)
        self.slp = Pin(slp_pin, Pin.OUT, value=0)
        self.slp.value(0)
        self.subs = {}
        self.connections = ''
        self.ignore = []
        self.callback = None


    async def chk(self):
        while True:
            while True:
                if not self.can.any():
                    break
                hdr, a, b, mess = self.can.recv()
                if hdr not in self.ignore:
                    print(hdr, mess)
                boards.iris.process(hdr, mess)

            await asyncio.sleep_ms(0)

    def send(self, data, arb_id):
        self.can.send(list(data), arb_id)

    def create_sub(self, msg):
        sub = struct.unpack('II', msg)
        self.subs[sub[0]] = sub[1] # sender: receiver

    def clear_subs(self, *args):
        self.subs = {}
        
    def create_callback(self, pid, callback):
        self.callback = callback
        self.subs[pid] = 69

    # -------------------------------------------------
    
class MqttMgr:
    def __init__(self,client_id, server, subs: list):
        self.client = MQTTClient(client_id, server)
        self.client.set_callback(self.cb)
        self.client.connect()
        for sub in subs:
            self.client.subscribe(sub)
        
    async def chk(self):
        while True:
            self.client.check_msg()
            await asyncio.sleep_ms(20)
        
    @staticmethod
    def cb(topic: bytearray, msg: bytearray):
        print(topic, msg)
    
    # -------------------------------------------------

class SDMgr:
    def __init__(self, slot):
        self.slot = slot
        self.mounted = False
        self.sd = None # card object
        self.html_list = '<p>no sd files</p>'

    def mount(self):
        if not self.mounted:
            self.sd = machine.SDCard(slot=self.slot)
            uos.mount(self.sd, "/sd")
        print('sd contents:')
        print(self.files)
        self.html_list = self.html_file_list()

    @property
    def files(self):
        return uos.listdir('/sd')

    def html_file_list(self):
        return ''.join(['<p>{}: {}</p>'.format(i, f) for i, f in enumerate(uos.listdir('/sd'))])

    def _open(self, filename):
        with open('/sd/{}'.format(filename), 'r') as self.f:
            for line in self.f:
                yield line.strip()

    def opener(self, filename):
        if type(filename) is int:
            print('opening with index')
            self.gen = self._open(self.files[filename])
        else:
            self.gen = self._open(filename)

    def readline(self):
        try:
            return next(self.gen)
        except StopIteration:
            print('eof')
            return None

    # -------------------------------------------------

class Button:
    def __init__(self, name, pin, pull_up, can_id, callback):
        self.name = name
        print(self.name)
        self.can_id = can_id + this_id
        if pull_up:
            self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        else:
            self.pin = Pin(pin, Pin.IN)
        self.state = not self.pin.value()
        self.callback = callback
        self.pack = 'B'

    def chk(self):
        if self.state == self.pin.value():
            self.state = not self.state
            self.callback(self)

    # -------------------------------------------------

class DigOUT:
    def __init__(self, name, pin):
        self.name = name
        self.pin = Pin(pin, Pin.OUT)
        self.pin.off()

    def can_write(self, msg):
        self.pin.value(struct.unpack('b', msg)[0])

    # -------------------------------------------------

class Analog:
    def __init__(self, name, pin, can_id, callback):
        self.name = name
        print(self.name)
        self.state = None
        self.can_id = can_id + this_id
        self.pin = ADC(Pin(pin))
        self.pin.atten(ADC.ATTN_11DB)
        self.pin.width(ADC.WIDTH_12BIT)
        self.old = int(self.pin.read()/16)
        self.pack = 'B'
        self.callback = callback
    def chk(self):
        self.state = int(self.pin.read()/16)
        global broadcast_state
        if abs(self.state - self.old) > 1:
            self.old = self.state
            print('{}: {} can_id: {}'.format(self.name, self.state, self.can_id))
            self.callback(self)

    # -------------------------------------------------
    
class Servo:
    def __init__(self, pin):
        self.pin = PWM(Pin(pin))
        self.pin.freq(50)
        self.pin.duty(90)

    def set(self, pos):
        pos = (pos - 255) * -1
        mapped = round(pos * .433) + 20
        self.pin.duty(mapped)

    # -------------------------------------------------
    
class NeoMgr:
    show = [(0, 33, 0), (0, 0, 33), (33, 0, 0), (0, 0, 0)]
    green = ((0, 10, 3), (1, 25, 6))
    blue = ((0, 3, 10), (1, 6, 25))
    red = ((11, 0, 0), (25, 0, 6))
    colors = (red, green, blue)

    rbow = tuple([int((math.sin(math.pi / 18 * i) * 127 + 128) / 10) for i in range(36)])

    def __init__(self, pin, num_pix):
        self.neo = NeoPixel(Pin(pin, Pin.OUT), num_pix)
        self.num_pix = num_pix
        self.fill(0,0,0)
        self.index = 0
        self.state = 'rainbow'
        self.chase_color = self.green
        self.slowdown = 5  # use this to slow down the 20ms time
        self.slowdown_count = 0

    def light_show(self, *args):
        for color in self.show:
            for p in range(self.num_pix):
                self.neo[p] = color
            self.neo.write()
            utime.sleep_ms(250)

    def fill(self, r, g, b):
        for p in range(self.num_pix):
            self.neo[p] = (r, g, b)
        self.neo.write()

    def can_fill(self, msg):
        self.fill(msg[0], msg[1], msg[2])

    def chk(self):
        if self.state == 'rainbow':
            self.rainbow()
        elif self.state == 'ring_chase':
            self.ring_chase()

    def rainbow(self):
        for i in range(self.num_pix):
            self.neo[i] = (self.rbow[self.index], self.rbow[(self.index + 12)%36], self.rbow[(self.index + 24)%36])
        self.neo.write()
        self.index = (self.index + 1) % 36

    def ring_chase(self):
        self.slowdown_count += 1
        self.slowdown_count = self.slowdown_count % self.slowdown
        if not self.slowdown_count:
            self.index += 1
            self.index = self.index % self.num_pix
            for i in range(self.num_pix):
                if self.index == i:
                    self.neo[i] = self.chase_color[1]
                else:
                    self.neo[i] = self.chase_color[0]
            self.neo.write()
