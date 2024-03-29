import esp32
import machine as upython
from machine import Pin, ADC, Timer, PWM, CAN
from neopixel import NeoPixel
import utime
import hx711
import struct

print('hx711 test code')
print('v1.0')
print('initializing')
this_id = 800
print(this_id)
broadcast_state = False
subscriptions = {}

upython.freq(240000000)


# Setup standard components
hbt_led = Pin(5, Pin.OUT, value=0)

func_button = Pin(36, Pin.IN) # Has external pullup

neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
neo_status[0] = (0, 0, 0)
neo_status.write()

a_button = Pin(21, Pin.IN, Pin.PULL_UP)
b_button = Pin(22, Pin.IN, Pin.PULL_UP)

# a_led = Pin(5, Pin.OUT, value=0)
b_led = Pin(23, Pin.OUT, value=0)

can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)

# Start CAN
can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.LOOPBACK, baudrate=250000)

buf = bytearray(8)
mess = [0, 0, 0, memoryview(buf)]

scale = hx711.HX711(d_out=19, pd_sck=18)
utime.sleep(1)
scale.tare()
print('scale started')


# Setup hbt timer
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
    elif id == 98:
        led_b.value(buf[0])
    elif id == 97:
        scale.tare()

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


    if not a_button.value():
        print('a button pressed')
        scale.check()
        utime.sleep_ms(50)
    if not b_button.value():
        print('b button pressed, taring scale')
        scale.tare()
        b_led.value(1)
        utime.sleep(.5)
        b_led.value(0)
        utime.sleep(.5)

    weight = scale.check()
    if weight:
        print('weight: {}, can_id: {}'.format(weight, (this_id+50)))
        if broadcast_state:
            can.send([weight], this_id + 50)

    utime.sleep_ms(20)
