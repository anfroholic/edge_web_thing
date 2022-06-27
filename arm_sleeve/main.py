import json
import utime
import machine
from utilities import *
import uasyncio as asyncio
import gc
gc.collect()
from machine import I2C
import struct

print('arm sleeve board')
print('v1.00p')
print('initializing')
this_id = 2000
print(this_id)
broadcast_state = False
subscriptions = {}

# Set up standard components
machine.freq(240000000)

hbt = HBT(pin=5, interval=500)
neo_status = NeoMgr(17, 1)




can = CanMgr(0, tx=4, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000, slp_pin=2)


i2c = I2C(0, scl=Pin(23), sda=Pin(22), freq=400000)


class NeoRing():
    interval = 100
    green = ((0, 10, 3), (1, 25, 6))
    blue = ((0, 3, 10), (1, 6, 25))
    red = ((11, 0, 0), (25, 0, 6))
    colors = (red, green, blue)

    def __init__(self, num_leds, pin):
        self.num_leds = num_leds
        self.pin = Pin(pin, Pin.OUT)
        self.neo = NeoPixel(self.pin, self.num_leds)
        self.index = 0
        self.start = utime.ticks_ms()
        self.state = 1

    def fill(self, r,g,b):
        for pixel in range(self.num_leds):
            self.neo[pixel] = (r, g, b)
        self.neo.write()

    def chk(self):
        if utime.ticks_diff(utime.ticks_ms(), self.start) > self.interval:
            self.start = utime.ticks_ms()
            self.index += 1
            self.index = self.index % self.num_leds
            for i in range(self.num_leds):
                if self.index == i:
                    self.neo[i] = self.colors[self.state][1]
                else:
                    self.neo[i] = self.colors[self.state][0]
            self.neo.write()


class Encoder:
    """
    AS5048B magnetic encoder
    https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf
    """
    resolution = 16384 # 14 bits
    half = 16384/2
    angle_register = int(0xFE)
    auto_gain_control_reg = int(0xFA)
    diagnostics_reg = int(0xFB)
    zero_reg = int(0x16)
    
    
    def __init__(self, name: str, address: int, invert: bool, offset: int):
        self.name = name
        self.address = address
        self.ring_size = 8
        self.ring = [0] * self.ring_size
        self.index = 0
        self.invert = invert
        self.offset = offset

    def chk(self) -> None:
        high, low = list(i2c.readfrom_mem(self.address, self.angle_register, 2))  # read from device
        self.index = (self.index + 1) % self.ring_size  # count around ring averager
        
        ang = (high << 6) + low - self.offset
        if ang > self.half:
            ang = ang - self.resolution
        self.ring[self.index] = ang  # add new value to ring
                
    @property
    def state(self):                    
        if self.invert:
            return -int(sum(self.ring)/self.ring_size) #average ring buffer and invert
        return int(sum(self.ring)/self.ring_size)
    
    @property
    def angle(self):
        return self.state/self.resolution * 360.0
            
    
    def get_gain(self):
        """ 255 is low field 0 is high field """
        return i2c.readfrom_mem(self.address, self.auto_gain_control_reg, 1)[0]
    
    def get_diag(self):
        raw = i2c.readfrom_mem(self.address, self.diagnostics_reg, 1)[0]
        return {'mag too low': bool(raw & 8),
                'mag too high': bool(raw & 4),
                'CORDIC Overflow': bool(raw & 2),
                'Offset Compensation finished': bool(raw & 1)
                }
    
    def set_zero(self):
        pos = i2c.readfrom_mem(self.address, self.angle_register, 2)
        utime.sleep_ms(10)
        i2c.writeto_mem(self.address, self.zero_reg, pos)

theta_coder = Encoder(name='mr_theta_coder', address=67, invert=True, offset=3076)
phi_coder = Encoder(name='mrs_phi_coder', address=64, invert=True, offset=3177)

neo_phi = NeoRing(pin=21, num_leds=12)
neo_theta = NeoRing(pin=13, num_leds=12)

def print_state(state, button):
    print(state, button.can_id)
    
def phi_color(state, *args):
    if state:
        neo_phi.state = (neo_phi.state + 1) % 3

def theta_color(state, *args):
    if state:
        neo_theta.state = (neo_theta.state + 1) % 3
    
func_button = Button('func button', 36, False, 54, print_state)
a_button = Button('a_button', 32, True, 50, phi_color)
b_button = Button('b_button', 33, True, 51, theta_color)


async def chk_hw():
    while True:
        hbt.chk()
        phi_coder.chk()
        theta_coder.chk()
        neo_phi.chk()
        neo_theta.chk()
        a_button.chk()
        b_button.chk()
        func_button.chk()
        await asyncio.sleep_ms(20)


async def post_angles():
    while True:
        # print(theta_coder.angle, phi_coder.angle)
        print('theta: {}, phi: {}'.format(theta_coder.angle, phi_coder.angle, 2))
        await asyncio.sleep_ms(100)
        
        
def this_show():
    leds = [led_0, led_1, led_2, led_3]
    for led in leds:
        led.value(1)
        utime.sleep_ms(300)
    for led in leds:
        led.value(0)


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



    else:
        print('unknown command')


neo_status.light_show()
neo_phi.fill(5,0,0)


while True:
    """make sure i2c devices are present"""
    found = True
    connected = i2c.scan()
    print(connected)
    if phi_coder.address not in connected:
        found = False
    if theta_coder.address not in connected:
        found = False
    if found:
        print('encoders present')
        break
    print('no encoder found')
    utime.sleep_ms(500)

neo_phi.fill(0,10,10)
        

async def main():
    asyncio.create_task(chk_hw())
    asyncio.create_task(post_angles())
    while True:
        await asyncio.sleep(5)

while True:
    asyncio.run(main())