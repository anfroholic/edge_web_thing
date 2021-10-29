import esp32
import machine
from machine import Pin, ADC, Timer, PWM, CAN
from neopixel import NeoPixel
import utime


print('stack light board test code')
print('v1.0')
print('initializing')

# Setup standard components
hbt_led = Pin(5, Pin.OUT, value=0)

func_button = Pin(36, Pin.IN) # Has external pullup

neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)


minus_button = Pin(23, Pin.IN, Pin.PULL_UP)
plus_button = Pin(33, Pin.IN, Pin.PULL_UP)
off_button = Pin(39, Pin.IN)
buzz_button = Pin(22, Pin.IN, Pin.PULL_UP)

white_led = Pin(25, Pin.OUT, value=0)
blue_led = Pin(26, Pin.OUT, value=0)
green_led = Pin(27, Pin.OUT, value=0)
yellow_led = Pin(14, Pin.OUT, value=0)
red_led = Pin(12, Pin.OUT, value=0)
buzzer = Pin(32, Pin.OUT, value=0)

can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)

# Start CAN
can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.LOOPBACK, baudrate=250000)

c_buf = bytearray(8)
c_mess = [0, 0, 0, memoryview(c_buf)]


print(machine.freq())
machine.freq(240000000)
print(machine.freq())


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


def send(mess, id):
    # can.send([1,2,3], 0x102)
    can.send(mess, id)

def get():
    if can.any():
        can.recv(c_mess)
    else:
        print('no messages')
    return c_mess

while True:
    chk_hbt()
    if not func_button.value():
        print('function button pressed')
        light_show()
    if can.any():
        neo_status[0] = (33, 0, 0)
        neo_status.write()
        utime.sleep_ms(250)
    if not minus_button.value():
        print('minus_button button pressed')
        light_show()
    if not plus_button.value():
        print('plus button pressed')
        light_show()
    if not buzz_button.value():
        print('buzz button pressed')
        buzzer.value(1)
        utime.sleep(.25)
        buzzer.value(0)
        utime.sleep(.25)
    if not off_button.value():
        print('off button pressed')
        light_show()
