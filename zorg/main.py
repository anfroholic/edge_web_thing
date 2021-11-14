#import esp32
import machine
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import struct
import uos

print('zorg board')
print('v1.00p')
print('initializing')
this_id = 100
print(this_id)
broadcast_state = False
subscriptions = {}

# Set up standard components
machine.freq(240000000)
hbt_led = Pin(5, Pin.OUT, value=0)

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

sd_init = False
cmd = Pin(15, Pin.PULL_UP)
sk = Pin(12, Pin.PULL_UP)
s1k = Pin(13, Pin.PULL_UP)


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


a_button = Button('a_button', 32, True, 50)
b_button = Button('b_button', 26, True, 51)
c_button = Button('c_button', 19, True, 52)
d_button = Button('d_button', 23, True, 53)
# sd_detect = Pin(18, Pin.IN, Pin.PULL_UP)
sd_detect = Button('sd_detect', 18, True, 54)

led_a = Pin(33, Pin.OUT, value=0)
led_b = Pin(25, Pin.OUT, value=0)
led_c = Pin(21, Pin.OUT, value=0)
led_d = Pin(22, Pin.OUT, value=0)


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
    print('doing show')
    led_a.value(1)
    utime.sleep_ms(300)
    led_b.value(1)
    utime.sleep_ms(300)
    led_c.value(1)
    utime.sleep_ms(300)
    led_d.value(1)
    utime.sleep_ms(300)
    led_a.value(0)
    led_b.value(0)
    led_c.value(0)
    led_d.value(0)

def light_show():
    neo_status[0] = (0, 33, 0)
    neo_bus[0] = (0, 33, 0)
    neo_bus.write()
    neo_status.write()
    utime.sleep_ms(250)
    neo_status[0] = (0, 0, 33)
    neo_bus[0] = (0, 0, 33)
    neo_bus.write()
    neo_status.write()
    utime.sleep_ms(250)
    neo_status[0] = (33, 0, 0)
    neo_bus[0] = (33, 0, 0)
    neo_bus.write()
    neo_status.write()
    utime.sleep_ms(250)
    neo_status[0] = (0, 0, 0)
    neo_bus[0] = (0, 0, 0)
    neo_bus.write()
    neo_status.write()

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

while True:
    chk_hbt()

    if(can.any()):
        get()

    if not func_button.value():
        print('function button pressed')
        broadcast_state = not broadcast_state
        broadcast(broadcast_state)
        utime.sleep_ms(200)
        if sd_init == False:
            sdd = machine.SDCard(slot=3)
            uos.mount(sdd, "/sd")
            print('sd contents:')
            print(uos.listdir('/sd'))

    a_button.check()
    b_button.check()
    c_button.check()
    d_button.check()
    sd_detect.check()