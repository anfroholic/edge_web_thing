
"""
version: 0.1
6/4/22
"""

from machine import Pin, ADC, CAN, UART
import utime
from neopixel import NeoPixel
import uos
import machine
import uasyncio as asyncio
import math

this_id = 0


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
    
class CanMgr:
    def __init__(self, bus, *, tx, rx, extframe, mode, baudrate, slp_pin):
        self.can = CAN(bus, tx=tx, rx=rx, extframe=extframe, mode=mode, baudrate=baudrate)
        self.slp = Pin(slp_pin, Pin.OUT, value=0)
        self.slp.value(0)
        self.buf = bytearray(8)
        self.msg = [0,0,0, memoryview(self.buf)]
        self.subscriptions = {}
        self.connections = ''
        
    async def chk(self):
        while True:
            while True:
                if not self.can.any():
                    break
                self.can.recv(self.msg)
                print(self.msg)
            await asyncio.sleep_ms(1)
            
    def send(self, data, arb_id):
        self.can.send(list(data), arb_id)
    
    def create_sub(self, sub):
        self.subscriptions[sub['brdcst']] = sub['sub']


class SDMgr:
    def __init__(self, slot):
        self.slot = slot
        self.mounted = False
        self.sd = None # card object
        self.html_list = None
        
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
        

class Button:
    def __init__(self, name, pin, pull_up, can_id, callback):
        self.name = name
        print(self.name)
        self.can_id = can_id + this_id
        if pull_up:
            self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        else:
            self.pin = Pin(pin, Pin.IN)
        self.state = self.pin.value()
        self.callback = callback

    def chk(self):
        global broadcast_state
        if self.state != self.pin.value():
            self.state = not self.state
            print('{} state: {} can_id: {}'.format(self.name, not self.state, self.can_id))
            self.callback(not self.state, self)


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
    def chk(self):
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


class HBT:
    def __init__(self, *, pin, interval):
        self.state = 0
        self.interval = interval
        self.pin = Pin(pin, Pin.OUT)
        self.next = utime.ticks_add(utime.ticks_ms(), self.interval)
        self.pin.value(self.state)

    def chk(self):
        if utime.ticks_diff(self.next, utime.ticks_ms()) <= 0:
            
            if self.state == 1:
                self.state = 0
                self.pin.value(self.state)
                
            else:
                self.state = 1
                self.pin.value(self.state)

            self.next = utime.ticks_add(self.next, self.interval)



class NeoMgr:
    show = [(0, 33, 0), (0, 0, 33), (33, 0, 0), (0, 0, 0)]

    rbow = tuple([int((math.sin(math.pi / 18 * i) * 127 + 128) / 10) for i in range(36)])
    print(rbow)

    def __init__(self, pin, num_pix):
        self.neo = NeoPixel(Pin(pin, Pin.OUT), num_pix)
        self.num_pix = num_pix
        self.fill(0,0,0)
        self.r_idx = 0
        self.state = 'rainbow'

    def light_show(self):
        for color in self.show:
            for p in range(self.num_pix):
                self.neo[p] = color
            self.neo.write()
            utime.sleep_ms(250)

    def fill(self, r, g, b):
        for p in range(self.num_pix):
            self.neo[p] = (r, g, b)
        self.neo.write()
        
    def chk(self):
        if self.state == 'rainbow':
            self.rainbow()
        
    def rainbow(self):
        for i in range(self.num_pix):
            self.neo[i] = (self.rbow[self.r_idx], self.rbow[(self.r_idx + 12)%36], self.rbow[(self.r_idx + 24)%36])
        self.neo.write()
        self.r_idx = (self.r_idx + 1) % 36


