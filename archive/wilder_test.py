from machine import Pin
import time
import machine

led = Pin(12, Pin.OUT)
r_forward = Pin(33, Pin.OUT)
r_reverse = Pin(25, Pin.OUT)
l_forward = Pin(27, Pin.OUT)
l_reverse = Pin(26, Pin.OUT)

print('it seems this code is running')
def blink():
    led.on()
    time.sleep(1)
    led.off()
    time.sleep(1)

def r_test():
    r_forward.on()
    time.sleep(1)
    r_forward.off()
    time.sleep(1)
    r_reverse.on()
    time.sleep(1)
    r_reverse.off()
    time.sleep(1)

def l_test():
    l_forward.on()
    time.sleep(1)
    l_forward.off()
    time.sleep(1)
    l_reverse.on()
    time.sleep(1)
    l_reverse.off()
    time.sleep(1)

blink()
blink()
blink()
blink()
blink()
blink()
