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

can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)

can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.LOOPBACK, baudrate=250000)

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
a_button_id = 0
b_button_state = 1
b_button_can_id = 1
a_button = Pin(22, Pin.IN, Pin.PULL_UP)
b_button = Pin(23, Pin.IN, Pin.PULL_UP)


# some_analog_prev = None
# some_analog_state = None
# some_analog_can_id = 9999  # this id is counting from 50 for broadcasts
# some_analog = ADC(Pin(9999))
# some_analog.atten(ADC.ATTN_11DB)
# some_analog.width(ADC.WIDTH_12BIT)



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
    servo.duty(pos)

def move_all_servos(pos):
    for servo in servo_label:
            move_servo(servo, pos)

def truth_fairy(state):
    s = False
    if state == 1:
        s = True
    return s

def get():
    can.recv(mess)
    print(str(mess[0]) + ', ' + str(buf[0]))

    # these are messages for all boards
    if mess[0] <= 100:
        if mess[0] == 1:
            light_show()
        elif mess[0] == 2:
            machine.reset()
        elif mess[0] == 3:
            neo_status[0] = (buf[0], buf[1], buf[2])
            neo_status.write()
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

    else:
        print('unknown command')

while True:
    chk_hbt()

    if(can.any()):
        get()

    if not func_button.value():
        print('function button pressed')
        broadcast_state != broadcast_state
        if broadcast_state:
            neo_status[0] = (0, 33, 0)
            neo_status.write()
        else:
            neo_status[0] = (0, 33, 0)
            neo_status.write()

    if a_button.value() != a_button_state:
        a_button_state = a_button.value()
        arb = self_broadcast + a_button_can_id
        can.send([a_state], arb)

    if b_button.value() != b_button_state:
        b_button_state = b_button.value()
        arb = self_broadcast + b_button_can_id
        can.send([b_state], arb)

    # analog reads
    # if abs(some_analog_sate - some_analog.read()) > 3:
    #     some_analog_prev = some_analog_state
    # if broadcast_state:
    #     can.send([some_analog_state], some_analog_can_id)
