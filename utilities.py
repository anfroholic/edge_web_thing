from machine import Pin, ADC
import utime
from neopixel import NeoPixel

this_id = 0
broadcast_state = False



class Button:
    def __init__(self, name, pin, pull_up, can_id):
        self.name = name
        print(self.name)
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

class HBT:
    def __init__(self, pin, interval):
        self.state = 0
        self.interval = interval
        self.pin = Pin(pin, Pin.OUT)
        self.next = utime.ticks_add(utime.ticks_ms(), self.interval)
        self.pin.value(self.state)

    def check(self):
        if utime.ticks_diff(self.next, utime.ticks_ms()) <= 0:
            if self.state == 1:
                self.state = 0
                self.pin.value(self.state)
                #print("hbt")
            else:
                self.state = 1
                self.pin.value(self.state)

            self.next = utime.ticks_add(self.next, self.interval)

class NeoStatus:
    show = [(0, 33, 0), (0, 0, 33), (33, 0, 0), (0, 0, 0)]

    def __init__(self, pin):
        self.neo = NeoPixel(Pin(pin, Pin.OUT), 1)
        self.neo[0] = (0, 0, 0)
        self.neo.write()

    def light_show(self):
        for color in self.show:
            self.neo[0] = color
            self.neo.write()
            utime.sleep_ms(250)

    def fill(self, color: tuple):
        self.neo[0] = color
        self.neo.write()
