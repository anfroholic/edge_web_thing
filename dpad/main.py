import esp32
import machine
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import machine

print('dpad board')
print('v1.00p')
print('initializing')
this_id = 500
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
a_button_state = 1
a_button_can_id = 0 # id + self_broadcast
a_button = Pin(23, Pin.IN, Pin.PULL_UP)

b_button_state = 1
b_button_can_id = 1
b_button = Pin(22, Pin.IN, Pin.PULL_UP)

up_state = 1
up_can_id = 2
up = Pin(25, Pin.IN, Pin.PULL_UP)


down_state = 1
down_can_id = 3
down = Pin(27, Pin.IN, Pin.PULL_UP)



left_state = 1
left_can_id = 4
left = Pin(33, Pin.IN, Pin.PULL_UP)


right_state = 1
right_can_id = 5
right = Pin(26, Pin.IN, Pin.PULL_UP)


push_state = 1
push_can_id = 6
push = Pin(32, Pin.IN, Pin.PULL_UP)

pot_a_prev = 0
pot_a_state = 0
pot_a_can_id = 7  # this id is counting from 50 for broadcasts
pot_a = ADC(Pin(34))
pot_a.atten(ADC.ATTN_11DB)
pot_a.width(ADC.WIDTH_12BIT)


pot_b_prev = 0
pot_b_state = 0
pot_b_can_id = 8  # this id is counting from 50 for broadcasts
pot_b = ADC(Pin(35))
pot_b.atten(ADC.ATTN_11DB)
pot_b.width(ADC.WIDTH_12BIT)

led_0 = Pin(15, Pin.OUT, value=0)
led_1 = Pin(18, Pin.OUT, value=0)
led_2 = Pin(19, Pin.OUT, value=0)
led_3 = Pin(21, Pin.OUT, value=0)




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
            led_0.value(buf[0])
        elif this_arb == 91:
            led_1.value(buf[0])
        elif this_arb == 92:
            led_2.value(buf[0])
        elif this_arb == 93:
            led_3.value(buf[0])

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

    if a_button.value() != a_button_state:
        a_button_state = a_button.value()
        arb = self_broadcast + a_button_can_id
        print('a_button state: ' + str(a_button_state))
        send(arb, [reverse(a_button_state)])

    if b_button.value() != b_button_state:
        b_button_state = b_button.value()
        arb = self_broadcast + b_button_can_id
        print('b_button state: ' + str(b_button_state))
        send(arb, [reverse(b_button_state)])

    if up.value() != up_state:
        up_state = up.value()
        arb = self_broadcast + up_can_id
        print('up state: ' + str(up_state))
        send(arb, [reverse(up_state)])

    if down.value() != down_state:
        down_state = down.value()
        arb = self_broadcast + down_can_id
        print('down state: ' + str(down_state))
        send(arb, [reverse(down_state)])

    if left.value() != left_state:
        left_state = left.value()
        arb = self_broadcast + left_can_id
        print('left state: ' + str(left_state))
        send(arb, [reverse(left_state)])

    if right.value() != right_state:
        right_state = right.value()
        arb = self_broadcast + right_can_id
        print('right state: ' + str(right_state))
        send(arb, [reverse(right_state)])

    if push.value() != push_state:
        push_state = push.value()
        arb = self_broadcast + push_can_id
        print('push state: ' + str(push_state))
        send(arb, [reverse(push_state)])

    pot_a_state = int(round(pot_a.read())/16)
    if abs(pot_a_prev - pot_a_state) > 1:
        # print(pot_a_state)
        pot_a_prev = pot_a_state
        send(pot_a_can_id + self_broadcast, [pot_a_state])

    pot_b_state = int(round(pot_b.read())/16)
    if abs(pot_b_prev - pot_b_state) > 1:
        # print(pot_b_state)
        pot_b_prev = pot_b_state
        send(pot_b_can_id + self_broadcast, [pot_b_state])
