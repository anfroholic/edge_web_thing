import esp32
import machine
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import machine

print('3d printhead board PNP version')
print('v1.00')
print('initializing')

# Set up standard components
machine.freq(240000000)
hbt_led = Pin(5, Pin.OUT, value=0)

func_button = Pin(36, Pin.IN) # Has external pullup

neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)


neo_ring_pin = Pin(33, Pin.OUT)
neo_ring = NeoPixel(neo_ring_pin, 12)

# Set up rest

#probe = Pin(35, Pin.IN)
#input_1 = Pin(32, Pin.IN, Pin.PULL_UP)
#input_2 = Pin(33, Pin.IN, Pin.PULL_UP)


analog_1 = ADC(Pin(34))
analog_1.atten(ADC.ATTN_11DB)
analog_1.width(ADC.WIDTH_12BIT)

thermister = ADC(Pin(39))
thermister.atten(ADC.ATTN_11DB)
thermister.width(ADC.WIDTH_12BIT)

heater = Pin(22, Pin.OUT, value=0)
fan = Pin(23, Pin.OUT, value=0)

uart1 = UART(1, baudrate=115200, stop=1, parity=None, bits=8, tx=32, rx=35)
can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.LOOPBACK, baudrate=250000)

c_buf = bytearray(8)
c_mess = [0, 0, 0, memoryview(c_buf)]

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

def feed_feeder(feeder):
    uart1.write(feeder)


def ring_light(state):
    if state:
        for i in range(12):
            neo_ring[i] = (50, 50, 50)
    else:
        for i in range(12):
            neo_ring[i] = (0,0,0)
    neo_ring.write()

def get():
    can.recv(c_mess)
    print(str(c_mess[0]) + ', ' + str(c_buf[0]))
    if c_mess[0] == 1:
        if c_buf[0] == 0:
            light_show()
        elif c_buf[0] == 1:
            machine.reset()
    elif c_mess[0] == 3:  # 3 is id for this board
        if c_buf[0] == 0:
            heater.value(0)
        elif c_buf[0] == 1:
            heater.value(1)

        elif c_buf[0] >= 2 and c_buf[0] <= 17:
            feed = str(c_buf[0])
            print(feed)
            feed_feeder(feed)

        elif c_buf[0] == 18:
            print('make neo light on function')
        elif c_buf[0] == 19:
            print('make neo light off function')
    else:
        print('unknown command')

while True:
    chk_hbt()

    if(can.any()):
        get()

    if uart1.any():
        print(uart1.readline())

    if not func_button.value():
        print('function button pressed')
        therm = thermister.read()
        utime.sleep_ms(10)
        analog = analog_1.read()
        print('thermister val: ' + str(therm))
        print('analog_1 val: ' + str(analog))
        light_show()
    # if probe.value():
    #     print('probe triggered')
    #     utime.sleep_ms(250)
        #light_show()
    # if not input_1.value():
    #     print('input_1 button pressed')
    #     utime.sleep_ms(250)
    #     #light_show()
    # if not input_2.value():
    #     print('input_2 button pressed')
    #     utime.sleep_ms(250)
