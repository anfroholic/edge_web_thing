import esp32
import machine
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import machine

print('Servo board')
print('v1.00p')
print('initializing')
this_id = 400
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
a_button = Pin(22, Pin.IN, Pin.PULL_UP)

b_button_state = 1
b_button_can_id = 1
b_button = Pin(23, Pin.IN, Pin.PULL_UP)


# Mistake!!! Servo 7 and 9 are not usable! Also Servo 12, we are OUT of PWM channels. There are a max of
servo_label = ['servo_1', 'servo_2', 'servo_3', 'servo_4', 'servo_6', 'servo_8', 'servo_10', 'servo_12']
servos = [26, 27, 25, 14, 12, 18, 19, 21]
servo_can_id = [81, 82, 83, 84, 86, 88, 90, 92]

for servo in range(len(servos)):
    print('set up servo {} on pin {}'.format(servo_label[servo], servos[servo]))
    servo_label[servo] = PWM(Pin(servos[servo]))
    servo_label[servo].freq(50)
    servo_label[servo].duty(90)

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

def move_servo(servo, pos):
    mapped = round((pos * .433) + 20)
    # servo.duty(mapped)
    print(mapped)

def move_all_servos(pos):
    for servo in servo_label:
            move_servo(servo, pos)

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


        elif this_arb in servo_can_id:
            print('move_servo')
            print(servo_can_id.index(this_arb))
            move_servo(servo_can_id.index(this_arb), buf[0])

        elif this_arb == 99:
            move_all_servos(buf[0])

    # # dpad pot_a
    # elif mess[0] == 557:
    #     move_servo('servo_1', buf[0])
    # # dpad pot_b
    # elif mess[0] == 558:
    #     move_servo('servo_2', buf[0])


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
