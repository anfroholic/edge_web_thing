import esp32
import machine
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import machine as upython
import struct

print('relay board')
print('v1.00p')
print('initializing')
this_id = 600
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

can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)

can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000)

buf = bytearray(8)
mess = [0, 0, 0, memoryview(buf)]

# Set up hbt timer
hbt_state = 0
hbt_interval = 500
start = utime.ticks_ms()
next_hbt = utime.ticks_add(start, hbt_interval)
hbt_led.value(hbt_state)

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


# Set up peripherals

button_1 = Button('button_1', 26, True, 50)
button_2 = Button('button_2', 25, True, 51)
button_3 = Button('button_3', 33, True, 53)
button_4 = Button('button_4', 32, True, 54)


relay_1 = Pin(22, Pin.OUT, value=0)
relay_2 = Pin(21, Pin.OUT, value=0)
relay_3 = Pin(19, Pin.OUT, value=0)
relay_4 = Pin(23, Pin.OUT, value=0)

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
    relay_1.value(1)
    utime.sleep_ms(300)
    relay_2.value(1)
    utime.sleep_ms(300)
    relay_3.value(1)
    utime.sleep_ms(300)
    relay_4.value(1)
    utime.sleep_ms(300)
    relay_1.value(0)
    relay_2.value(0)
    relay_3.value(0)
    relay_4.value(0)



def light_show():
    neo_status[0] = (0, 33, 0)
    neo_status.write()
    utime.sleep_ms(250)
    neo_status[0] = (0, 0, 33)
    neo_status.write()
    utime.sleep_ms(250)
    neo_status[0] = (33, 0, 0)
    neo_status.write()
    utime.sleep_ms(250)
    neo_status[0] = (0, 0, 0)
    neo_status.write()

def broadcast(state):
    if state:
        neo_status[0] = (0, 10, 0)
        neo_status.write()
    else:
        neo_status[0] = (0, 0, 0)
        neo_status.write()

def reverse(state):
    if state == 0:
        state = 1
    else:
        state = 0
    return state

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

    elif id == 90:
        relay_1.value(buf[0])
    elif id == 91:
        relay_2.value(buf[0])
    elif id == 92:
        relay_3.value(buf[0])
    elif id == 93:
        relay_4.value(buf[0])

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

    button_1.check()
    button_2.check()
    button_3.check()
    button_4.check()
