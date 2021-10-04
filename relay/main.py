import esp32
import machine
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import machine

print('relay board')
print('v1.00p')
print('initializing')
this_id = 600
print(this_id)
broadcast_state = False
self_broadcast = this_id + 50

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



# Set up peripherals
button_1_state = 1
button_1_can_id = 0 # id + self_broadcast
button_1 = Pin(33, Pin.IN, Pin.PULL_UP)

button_2_state = 1
button_2_can_id = 1
button_2 = Pin(32, Pin.IN, Pin.PULL_UP)

relay_1 = Pin(22, Pin.OUT, value=0)
relay_2 = Pin(21, Pin.OUT, value=0)
relay_3 = Pin(19, Pin.OUT, value=0)
relay_4 = Pin(23, Pin.OUT, value=0)




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
    # print(str(mess[0]) + ', ' + str(buf[0]))

    # these are messages for all boards
    if mess[0] <= 100:
        if mess[0] == 1:
            light_show()
        elif mess[0] == 2:
            machine.reset()
        elif mess[0] == 3:
            neo_status[0] = (buf[0], buf[1], buf[2])
            neo_status.write()
        elif mess[0] == 4:
            global broadcast_state
            broadcast_state = buf[0]
            broadcast(broadcast_state)

    # messages to self
    elif mess[0] >= this_id and mess[0] <= (this_id+99):
        this_arb = mess[0] - this_id
        if this_arb == 1:
            light_show()
        elif this_arb == 2:
            machine.reset()
        elif this_arb == 3:
            neo_status[0] = (buf[0], buf[1], buf[2])
            neo_status.write()
        elif mess[0] == 4:
            global broadcast_state
            broadcast_state = buf[0]
            broadcast(broadcast_state)

        elif this_arb == 90:
            relay_1.value(buf[0])
        elif this_arb == 91:
            relay_2.value(buf[0])
        elif this_arb == 92:
            relay_3.value(buf[0])
        elif this_arb == 93:
            relay_4.value(buf[0])

    # else:
    #     print('unknown command')

while True:
    chk_hbt()

    if(can.any()):
        get()

    if not func_button.value():
        print('function button pressed')
        broadcast_state = not broadcast_state
        broadcast(broadcast_state)
        utime.sleep_ms(200)

    if button_1.value() != button_1_state:
        button_1_state = button_1.value()
        arb = self_broadcast + button_1_can_id
        print('button_1 state: ' + str(button_1_state))
        send(arb, [reverse(button_1_state)])

    if button_2.value() != button_2_state:
        button_2_state = button_2.value()
        arb = self_broadcast + button_2_can_id
        print('button_2 state: ' + str(button_2_state))
        send(arb, [reverse(button_2_state)])
