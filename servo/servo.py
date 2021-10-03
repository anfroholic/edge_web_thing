import esp32
import machine
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import machine

print('3d printhead board PNP version')
print('v1.00')
print('initializing')
this_id = 400

# Set up standard components
machine.freq(240000000)
hbt_led = Pin(5, Pin.OUT, value=0)

func_button = Pin(36, Pin.IN) # Has external pullup

neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)


can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.LOOPBACK, baudrate=250000)

buf = bytearray(8)
mess = [0, 0, 0, memoryview(buf)]

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

    elif mess[0] >= this_id and mess[0] <= (this_id+99):
        this_arb = mess[0] - this_id
        if this_arb == 1:
            light_show()
        elif this_arb == 2:
            machine.reset()
        elif this_arb == 3:
            neo_status[0] = (buf[0], buf[1], buf[2])
            neo_status.write()



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
