import esp32
import machine as upython
from machine import Pin, ADC, Timer, PWM, UART, CAN, I2C, SoftI2C
from neopixel import NeoPixel
import utime
import struct

print('color_sensor')
print('v1.00p')
print('initializing')
this_id = 2100
print(this_id)
broadcast_state = False
subscriptions = {}

# Set up standard components
upython.freq(240000000)
hbt_led = Pin(5, Pin.OUT, value=0)

func_button = Pin(36, Pin.IN) # Has external pullup

neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
neo_status[0] = (0, 0, 0)
neo_status.write()

can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)

can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000)

buf = bytearray(8)
mess = [0, 0, 0, memoryview(buf)]

i2c = SoftI2C(scl=Pin(21), sda=Pin(19), freq=80000)

# i2c = I2C(1, scl=Pin(21), sda=Pin(19), freq=70000)

class VEML6040:
    adr = 16

    # registers
    cmd_reg = 0

    red = int(0x08)
    green = int(0x09)
    blue = int(0x0A)
    white = int(0x0B)

    # color_regs = {'red': red, 'green': green, 'blue': blue, 'white': white}
    color_regs = [red, green, blue, white]

    command = 6

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.start = utime.ticks_ms()
        self.interval = 100 # ms
        self.integration_time = 60 # ms

    def check(self):
        if utime.ticks_diff(utime.ticks_ms(), self.start) > self.interval:
            self.start = utime.ticks_ms()
            self.trigger()
            utime.sleep_ms(self.integration_time)
            print(self.getRGB())

    def trigger(self):
        self.port.writeto_mem(self.adr, self.cmd_reg, b'\x06\x00')

    def read(self, register):
        utime.sleep_ms(5)
        # try:
        val = struct.unpack('H', self.port.readfrom_mem(self.adr, register, 2))[0]
        # except OSError:
        #     pass
        return val

    def getRGB(self):
        return [self.read(reg) for reg in self.color_regs]

sen = VEML6040('sensor', i2c)
sen.trigger()
print('booting')
utime.sleep(5)
print('booted')

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
            else:
                buf[0] = 0
            print('latch: {} on id: {}'.format(buf[0], self.broadcast_id))
            if self.can_id + 1 + this_id in subscriptions:
                process(subscriptions[self.broadcast_id])
operator = Operator('_latch', 40, 41)

a_button = Button('a_button', 33, True, 50)
b_button = Button('b_button', 23, True, 51)
input_a = Button('input_a', 32, True, 52)

led_a = Pin(25, Pin.OUT, value=0)
led_b = Pin(26, Pin.OUT, value=0)




# Set up hbt timer
hbt_state = 0
hbt_interval = 500
start = utime.ticks_ms()
next_hbt = utime.ticks_add(start, hbt_interval)
hbt_led.value(hbt_state)

def chk_hbt():
    global next_hbt
    global hbt_state
    now = utime.ticks_ms()
    if utime.ticks_diff(next_hbt, now) <= 0:
        if hbt_state == 1:
            hbt_state = 0
            hbt_led.value(hbt_state)
            #print("hbt")
        else:
            hbt_state = 1
            hbt_led.value(hbt_state)

        next_hbt = utime.ticks_add(next_hbt, hbt_interval)

def this_show():
    leds = [led_a, led_b]
    for led in leds:
        led.value(1)
        utime.sleep_ms(300)
    for led in leds:
        led.value(0)



def light_show():
    show = [(0, 33, 0), (0, 0, 33), (33, 0, 0), (0, 0, 0)]
    for color in show:
        neo_status[0] = color
        neo_status.write()
        utime.sleep_ms(250)

def broadcast(state):
    if state:
        neo_status[0] = (0, 10, 0)
        neo_status.write()
    else:
        neo_status[0] = (0, 0, 0)
        neo_status.write()

def send(arb, msg):
    global broadcast_state
    if broadcast_state:
        can.send(msg, arb)

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
        upython.reset()
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


light_show()
while True:
    chk_hbt()

    if(can.any()):
        get()

    if not func_button.value():
        print('function button pressed')
        broadcast_state = not broadcast_state
        broadcast(broadcast_state)
        utime.sleep_ms(200)

    a_button.check()
    b_button.check()
    sen.check()
