from machine import Pin
from neopixel import NeoPixel
import utime

import wlan

def light_show():
    show = [(0, 33, 0), (0, 0, 33), (33, 0, 0), (0, 0, 0)]
    for color in show:
        neo_status[0] = color
        neo_status.write()
        utime.sleep_ms(250)

hbt_led = Pin(5, Pin.OUT)

func_button = Pin(36, Pin.IN) # Has external pullup

neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
light_show()

print('starting wlan')

if wlan.connect():
    neo_status[0] = (0, 10, 2)
    neo_status.write()
else:
    neo_status[0] = (10, 0, 0)
    neo_status.write()
