import esp32
import machine as upython
from machine import Pin, ADC, Timer, PWM, UART, CAN
from neopixel import NeoPixel
import utime
import struct

print('thermocouple board')
print('v1.00p')
print('initializing')
this_id = 1300
print(this_id)
broadcast_state = False
subscriptions = {}

# Set up standard components
upython.freq(240000000)
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

    def check(self):
        global broadcast_state
        if self.state != self.pin.value():
            self.state = not self.state
            print('{} state: {} can_id: {}'.format(self.name, not self.state, self.can_id))
            if broadcast_state:
                can.send([not self.state], self.can_id)

class Analog:
    def __init__(self, name, pin, can_id):
        self.name = name
        print(self.name)
        self.state = None
        self.can_id = can_id + this_id
        self.pin = ADC(Pin(pin))
        self.pin.atten(ADC.ATTN_11DB)
        self.pin.width(ADC.WIDTH_12BIT)
        self.old = int(self.pin.read()/16)
    def check(self):
        self.state = int(self.pin.read()/16)
        global broadcast_state
        if abs(self.state - self.old) > 1:
            self.old = self.state
            print('{}: {} can_id: {}'.format(self.name, self.state, self.can_id))
            if broadcast_state:
                can.send([self.state], self.can_id)

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


a_button = Button('a_button', 25, True, 51)
b_button = Button('b_button', 26, True, 52)
c_button = Button('c_button', 15, True, 53)


input_a = Button('input_a', 32, True, 54)
input_b = Button('input_b', 33, True, 55)

#pot_a = Analog('a_pot', 32, 57)
# pot_b = Analog('b_pot', 35, 58)
#
output_a = Pin(23, Pin.OUT, value=0)
output_b = Pin(22, Pin.OUT, value=0)
# led_2 = Pin(19, Pin.OUT, value=0)
# led_3 = Pin(21, Pin.OUT, value=0)

class MAX6675():
    def __init__(self, so_pin=19, cs_pin=21, sck_pin=18):
        self.cs = Pin(cs_pin, Pin.OUT)
        self.so = Pin(so_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT)

        self.cs.on()
        self.so.off()
        self.sck.off()

        self.last_read_time = utime.ticks_ms()
        self.read_delay_ms = 500
        self.next_read_time = utime.ticks_ms()
        self.previous = None
        self.state = self.readCelsius()
        self.can_id = this_id + 50
        utime.sleep_ms(500)

    def readFahrenheit(self):
        return self.readCelsius() * 9.0 / 5.0 + 32

    def readCelsius(self):
        data = self.__read_data()
        volts = sum([b * (1 << i) for i, b in enumerate(reversed(data))])
        # print(volts)

        return volts * 0.25

    def __read_data(self):
        # CS down, read bytes then cs up
        self.cs.off()
        utime.sleep_us(10)
        data = self.__read_word() # (self.__read_byte() << 8) | self.__read_byte()
        self.cs.on()

        # print(data)
        # print(data[1:-3])

        if data[-3] == 1:
            print('no thermocouple')
            # raise NoThermocoupleAttached()

        return data[1:-3]

    def __read_word(self):
        return [self.__read_bit() for _ in range(16)]


    def __read_bit(self):
        self.sck.off()
        utime.sleep_us(10)
        bit = self.so.value()
        self.sck.on()
        utime.sleep_us(10)
        return bit

    def check(self):
        now = utime.ticks_ms()
        if utime.ticks_diff(self.next_read_time, now) <= 0:
            self.state = int(self.readCelsius())
            if not self.previous == self.state:
                print('temp is {} deg C'.format(self.state))
                self.previous = self.state
                if broadcast_state:
                    can.send([self.state], self.can_id)
            self.next_read_time = utime.ticks_add(self.next_read_time, self.read_delay_ms)


therm = MAX6675()

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

def this_show():
    print('doing show')
    led_0.value(1)
    utime.sleep_ms(300)
    led_1.value(1)
    utime.sleep_ms(300)
    led_2.value(1)
    utime.sleep_ms(300)
    led_3.value(1)
    utime.sleep_ms(300)
    led_0.value(0)
    led_1.value(0)
    led_2.value(0)
    led_3.value(0)

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
    # print(str(mess[0]) + ', ' + str(buf[0]))

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
        output_a.value(buf[0])
    elif id == 91:
        output_b.value(buf[0])

    else:
        print('unknown command')

while True:
    chk_hbt()

    if(can.any()):
        get()

    if not func_button.value():
        print('function button pressed')
        broadcast_state = not broadcast_state
        broadcast(broadcast_state)
        utime.sleep_ms(200)

    a_button.check()
    b_button.check()
    c_button.check()
    input_a.check()
    input_b.check()
    therm.check()
