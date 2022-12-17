import config
from machine import DAC, Pin
import uasyncio as asyncio
from boards.utilities import *
import boards.iris as iris



#Setup LCD

led_0 = DigOUT('led_0', 15)
led_1 = DigOUT('led_1', 18)
led_2 = DigOUT('led_2', 19)
led_3 = DigOUT('led_3', 21)


hw = [
    Button('button_a', 23, True, 50, callback=iris.button_sender),
    Button('button_b', 22, True, 51, callback=iris.button_sender),
    Button('up', 25, True, 52, callback=iris.button_sender),
    Button('down', 27, True, 53, callback=iris.button_sender),
    Button('left', 33, True, 54, callback=iris.button_sender),
    Button('right', 26, True, 55, callback=iris.button_sender),
    Button('push', 32, True, 56, callback=iris.button_sender),
    Analog('analog_a', 34, 57, callback=iris.button_sender),
    Analog('analog_b', 35, 58, callback=iris.button_sender)
    ]

async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(20)
        
    # -------------------------------------------------
    
def this_show(*args):
    lights = [led_0, led_1, led_2, led_3]
    for light in lights:
        light.pin.on()
        utime.sleep_ms(500)
        light.pin.off()
        
    # -------------------------------------------------
    
this = {
    79: this_show,
    90: led_0.can_write,
    91: led_1.can_write,
    92: led_2.can_write,
    93: led_3.can_write
    }
iris.things.update(this)