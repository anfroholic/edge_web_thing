import boards.iris as iris
import machine
import struct
from boards.utilities import *
import uasyncio as asyncio
import config
import lego





neo_bus = NeoMgr(27, 2)
neo_bus.fill(0,0,0)

led_a = DigOUT('led_a', 33)
led_b = DigOUT('led_b', 25)
led_c = DigOUT('led_c', 21)
led_d = DigOUT('led_d', 22)

hw = [
    Button(pin=34, name='a_button', pull_up=True, can_id=50, callback=iris.button_sender),
    Button(pin=26, name='b_button', pull_up=True, can_id=51, callback=iris.button_sender),
    Button(pin=14, name='c_button', pull_up=True, can_id=52, callback=iris.button_sender),
    Button(pin=12, name='d_button', pull_up=True, can_id=53, callback=iris.button_sender)
    ]

async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(20)
        
    # -------------------------------------------------
    
def this_show(*args):
    lights = [led_a, led_b, led_c, led_d]
    for light in lights:
        light.pin.on()
        utime.sleep_ms(500)
        light.pin.off()
        
    # -------------------------------------------------

this = {
    69: lego.do_it,
    79: this_show,
    90: led_a.can_write,
    91: led_b.can_write,
    92: led_c.can_write,
    93: led_d.can_write,
    94: neo_bus.light_show,
    95: neo_bus.fill
    }
iris.things.update(this)

    # -------------------------------------------------

import boards.webpage



