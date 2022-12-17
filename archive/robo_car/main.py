import esp32
import machine as upython
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import struct

print('robo car board')
print('v1.00p')
print('initializing')
this_id = 1500
print(this_id)
broadcast_state = False
subscriptions = {}



# Set up standard components
upython.freq(240000000)

MOTOR_DUTY = 700

motor_a_1 = PWM(Pin(33), freq=15000, duty=0)
motor_a_2 = PWM(Pin(25), freq=15000, duty=0)
motor_b_1 = PWM(Pin(13), freq=15000, duty=0)
motor_b_2 = PWM(Pin(18), freq=15000, duty=0)
motor_c_1 = PWM(Pin(26), freq=15000, duty=0)
motor_c_2 = PWM(Pin(27), freq=15000, duty=0)
motor_d_1 = PWM(Pin(12), freq=15000, duty=0)
motor_d_2 = PWM(Pin(19), freq=15000, duty=0)

# utime.sleep_ms(100)
motor_a_1.duty(0)
motor_a_2.duty(0)
motor_b_1.duty(0)
motor_b_2.duty(0)
motor_c_1.duty(0)
motor_c_2.duty(0)
motor_d_1.duty(0)
motor_d_2.duty(0)




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


neo_bar_pin = Pin(15, Pin.OUT)
neo_bar = NeoPixel(neo_bar_pin, 5)
def set_bar(r,g,b):
    for i in range(5):
        neo_bar[i] = (r, g, b)
    neo_bar.write()

set_bar(0,0,0)

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





class Motor:
    def __init__(self, name, f, r, duty):
        self.name = name
        self.f = f
        self.r = r
        self.duty = duty

    def move(self, speed):
        if 120 < speed < 136:
            self.f.duty(0)
            self.r.duty(0)
        elif speed < 125:
            self.f.duty(0)
            self.r.duty((128 - speed) * 8)
            print((128 - speed) * 8)
        else:
            self.f.duty((speed - 128) * 8)
            self.r.duty(0)
            print((speed - 128) * 8)


    def forward(self):
        self.f.duty(self.duty)
        self.r.duty(0)

    def reverse(self):
        self.f.duty(0)
        self.r.duty(self.duty)

    def stop(self):
        self.f.duty(0)
        self.r.duty(0)

motor_a = Motor('motor_a', motor_a_1, motor_a_2, MOTOR_DUTY)
motor_b = Motor('motor_b', motor_b_1, motor_b_2, MOTOR_DUTY)
motor_c = Motor('motor_c', motor_c_1, motor_c_2, MOTOR_DUTY)
motor_d = Motor('motor_d', motor_d_1, motor_d_2, MOTOR_DUTY)


# a_button = Button('a_button', 23, True, 50)
# b_button = Button('b_button', 22, True, 51)
# up = Button('up button', 25, True, 52)
# down = Button('down_button', 27, True, 53)
# left = Button('left_button', 33, True, 54)
# right = Button('right_button', 26, True, 55)
# push = Button('push_button', 32, True, 56)
#
analog_a = Analog('analog_a', 39, 50)
analog_b = Analog('analog_b', 35, 51)
analog_c = Analog('analog_c', 34, 52)
analog_d = Analog('analog_d', 32, 53)

input_a = Button('input_a', 21, True, 54)
input_b = Button('input_b', 22, True, 55)
input_c = Button('input_c', 14, True, 56)
input_d = Button('input_d', 23, True, 57)





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
    set_bar(0, 33, 0)
    utime.sleep_ms(250)
    set_bar(0, 0, 33)
    utime.sleep_ms(250)
    set_bar(33, 0, 0)
    utime.sleep_ms(250)
    set_bar(0, 0, 0)


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

    elif id == 80:
        motor_a.move(buf[0])
        motor_c.move(buf[0])
    elif id == 81:
        motor_b.move(-(buf[0]-255))
        motor_d.move(-(buf[0]-255))

        

    elif id == 90:
        if buf[0] == 1:
            motor_a.forward()
        else:
            motor_a.stop()
    elif id == 91:
        if buf[0] == 1:
            motor_a.reverse()
        else:
            motor_a.stop()

    elif id == 92:
        if buf[0] == 1:
            motor_b.forward()
        else:
            motor_b.stop()
    elif id == 93:
        if buf[0] == 1:
            motor_b.reverse()
        else:
            motor_b.stop()

    elif id == 94:
        if buf[0] == 1:
            motor_c.forward()
        else:
            motor_c.stop()
    elif id == 95:
        if buf[0] == 1:
            motor_c.reverse()
        else:
            motor_c.stop()

    elif id == 96:
        if buf[0] == 1:
            motor_d.forward()
        else:
            motor_d.stop()
    elif id == 97:
        if buf[0] == 1:
            motor_d.reverse()
        else:
            motor_d.stop()

    else:
        print('unknown command')


light_show()
this_show()

while True:
    chk_hbt()

    if(can.any()):
        get()

    if not func_button.value():
        print('function button pressed')
        broadcast_state = not broadcast_state
        broadcast(broadcast_state)
        utime.sleep_ms(200)

    # analog_a.check()
    # analog_b.check()
    # analog_c.check()
    # analog_d.check()

    input_a.check()
    input_b.check()
    input_c.check()
    input_d.check()
