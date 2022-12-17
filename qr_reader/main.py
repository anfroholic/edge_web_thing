import esp32
import machine as upython
from machine import Pin, ADC, Timer, PWM, UART, CAN
import utime
import struct
import json

from utilities import *
import utilities

print('qr reader board')
print('v1.00')
print('initializing')
utilities.this_id = 500
print(utilities.this_id)
utilities.broadcast_state = False
subscriptions = {}


# Set up standard components
upython.freq(240000000)

func_button = Pin(36, Pin.IN) # Has external pullup

buzz = PWM(Pin(25))
buzz.duty(0)
buzz.freq(2500)

neo_status = NeoStatus(pin=17)
hbt = HBT(pin=5, interval=500)

a_button = Button('a_button', 22, True, 50)
operator = Operator('_latch', 40, 41)

can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)
can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000)

buf = bytearray(8)
mess = [0, 0, 0, memoryview(buf)]

uart1 = UART(1, baudrate=115200, tx=21, rx=19)



read_button = Pin(23, Pin.IN, Pin.PULL_UP)
led = Pin(26, Pin.IN)

led_a = Pin(18, Pin.OUT, value=0)
read_led = Pin(33, Pin.OUT, value=0)

trig = Pin(32, Pin.OUT)
trig.on()





def broadcast(state):
    if state:
        neo_status.fill((0, 10, 0))
    else:
        neo_status.fill((0, 0, 0))


def send(arb, msg):
    if utilities.broadcast_state:
        can.send(msg, arb)

def get():
    can.recv(mess)
    #is this message for this board?
    if mess[0] < 100 or (mess[0] >= this_id and mess[0] <= (this_id+99)):
        process(mess[0]%100)
    #is message a subscription?
    if mess[0] in subscriptions:
        process(subscriptions[mess[0]])

def process(id):
    print(id)
    if id == 1:
        neo_status.light_show()
    elif id == 2:
        upython.reset()
    elif id == 3:
        neo_status.fill((buf[0], buf[1], buf[2]))
    elif id == 4:
        utilities.broadcast_state = buf[0]
        broadcast(utilities.broadcast_state)
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



neo_status.light_show()
while True:
    hbt.check()

    if(can.any()):
        get()

    if not func_button.value():
        print('function button pressed')
        utilities.broadcast_state = not utilities.broadcast_state
        broadcast(utilities.broadcast_state)
        utime.sleep_ms(200)

    a_button.check()


    if not read_button.value():
        read_led.on()
        trig.off()
        utime.sleep_ms(60)
    else:
        read_led.off()
        trig.on()

    if led.value():
        led_a.on()
    else:
        led_a.off()

    if uart1.any():
        print(uart1.readline().decode('ascii').strip('\r'))
        buzz.duty(512)
        utime.sleep_ms(300)
        buzz.duty(0)
