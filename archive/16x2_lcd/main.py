import esp32
import machine
from machine import Pin, ADC, Timer, PWM, CAN, DAC
from neopixel import NeoPixel
import utime
import lcd_api
import pyb_gpio_lcd
import struct


print('16 x 2 board test code')
print('v1.0')
print('initializing')

this_id = 700
print('device id' + str(this_id))
broadcast_state = False
self_broadcast = this_id + 50
subscriptions = {}

# Setup standard components
hbt_led = Pin(5, Pin.OUT, value=0)

func_button = Pin(36, Pin.IN) # Has external pullup

neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)

can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)

# Start CAN
can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.LOOPBACK, baudrate=250000)

buf = bytearray(8)
mess = [0, 0, 0, memoryview(buf)]


print(machine.freq())
machine.freq(240000000)
print(machine.freq())


dac = Pin(25, Pin.OUT, value=0)
#Setup LCD
lcd = pyb_gpio_lcd.GpioLcd(rs_pin=27,
                  enable_pin=14,
                  d0_pin=12,
                  d1_pin=13,
                  d2_pin=15,
                  d3_pin=18,
                  d4_pin=19,
                  d5_pin=21,
                  d6_pin=22,
                  d7_pin=23,
                  num_lines=2, num_columns=16)

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

    def check(self, broadcast):
        if self.state != self.pin.value():
            self.state = not self.state
            print('{} state: {} can_id: {}'.format(self.name, not self.state, self.can_id))
            lcd.clear()
            lcd.putstr('{} state: {}'.format(self.name, not self.state))
            if broadcast:
                can.send([not self.state], self.can_id)


a_button = Button('a_button', 39, False, 50)
b_button = Button('b_button', 34, False, 51)
down_button = Button('down_button', 35, False, 53)
up_button = Button('up_button', 33, True, 52)
left_button = Button('left_button', 26, True, 54)
right_button = Button('right_button', 32, True, 55)


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

class LCD:
    def __init__(self):
        self.interval = 5000
        self.start = utime.ticks_ms()
        self.next_update = utime.ticks_add(self.start, self.interval)
        self.lcd_0_0 = ''
        self.lcd_0_1 = ''
        self.lcd_1_0 = ''
        self.lcd_1_1 = ''
        self.line_0 = ''
        self.line_1 = ''
        self.text = ''

    def check(self):
        now = utime.ticks_ms()
        if utime.ticks_diff(self.next_update, now) <= 0:
            self.update()
            self.next_update = utime.ticks_add(self.next_update, self.interval)

    def update(self):
        self.line_0 = ''
        self.line_0 += self.lcd_0_0
        self.line_0 += self.lcd_0_1
        if len(self.line_0) > 16:
            self.line_0[:16]
        if len(self.line_0) < 16:
            for i in range(16 - len(self.line_0)):
                self.line_0 += ' '
        lcd.move_to(0,0)
        lcd.putstr(self.line_0)

        self.line_1 = ''
        self.line_1 += self.lcd_1_0
        self.line_1 += self.lcd_1_1
        if len(self.line_1) < 16:
            for i in range(16 - len(self.line_1)):
                self.line_1 += ' '
        lcd.move_to(0,1)
        lcd.putstr(self.line_1)

_lcd = LCD()

# Setup hbt timer
hbt_state = 0
hbt_interval = 500
start = utime.ticks_ms()
next_hbt = utime.ticks_add(start, hbt_interval)
hbt_led.value(hbt_state)

lcd.move_to(0,0)
lcd.putstr('16x2 LCD Booted')

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

def send(mess, id):
    # can.send([1,2,3], 0x102)
    can.send(mess, id)

def get():
    can.recv(mess)
    print(mess)
    if mess[0] < 100 or (mess[0] >= this_id and mess[0] <= (this_id+99)):
        process(mess[0]%100)
    if mess[0] in subscriptions:
        process(subscriptions[mess[0]])
    # print(str(mess[0]) + ', ' + str(buf[0]))

    # these are messages for all boards
def clear_buf():
    global buf
    for i in range(8):
        buf[i] = 0

def process(id):
    print(id)
    if id == 1:
        light_show()
    elif id == 2:
        machine.reset()
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
        #clear_buf()

    elif id == 91:
        print(buf)
        length = 0
        for i in range(len(buf)):
            print(buf[i])
            if buf[i] != 0:
                length += 1
            else:
                break
        s = "{}s".format(str(length))
        st = struct.unpack(s, buf)
        _lcd.lcd_0_0 = st[0].decode('ascii')
        _lcd.update()
        clear_buf()

    elif id == 92:
        print(buf)
        this = struct.unpack('B', buf)
        print(this[0])
        _lcd.lcd_0_1 = str(this[0])
        _lcd.update()
        clear_buf()

    elif id == 93:
        print(buf)
        length = 0
        for i in range(len(buf)):
            print(buf[i])
            if buf[i] != 0:
                length += 1
            else:
                break

        s = "{}s".format(str(length))
        print(s)
        st = struct.unpack(s, buf)
        print(st)
        _lcd.lcd_1_0 = st[0].decode('ascii')
        _lcd.update()
        clear_buf()

    elif id == 94:
        print(buf)
        this = struct.unpack('B', buf)
        print(this[0])
        _lcd.lcd_1_1 = str(this[0])
        _lcd.update()
        clear_buf()

    elif id == 99:
        lcd.move_to(0,0)
        text = ''
        for byte in range(8):
            text += str(int(buf[byte])) + ','
        lcd.putstr(text)
        clear_buf()
    elif id == 98:
        lcd.move_to(0,1)
        text = ''
        for byte in range(8):
            text += str(int(buf[byte])) + ','
        lcd.putstr(text)
        clear_buf()



    else:
        print('unknown command')




light_show()
while True:
    chk_hbt()
    _lcd.check()
    if not func_button.value():
        print('function button pressed')
        broadcast_state = not broadcast_state
        broadcast(broadcast_state)
        utime.sleep_ms(400)
    if can.any():
        get()
    a_button.check(broadcast_state)
    b_button.check(broadcast_state)
    up_button.check(broadcast_state)
    down_button.check(broadcast_state)
    left_button.check(broadcast_state)
    right_button.check(broadcast_state)
