import config
import uasyncio as asyncio
from boards.utilities import *
import boards.iris as iris
import utime


#Setup LCD

red = DigOUT('red', 12)
yellow = DigOUT('yellow', 14)
green = DigOUT('green', 27)
blue = DigOUT('blue', 26)
white = DigOUT('white', 25)
buzz = DigOUT('buzz', 32)

hw = [
    Button('buzz', 22, True, 51, callback=iris.button_sender),
    Button('minus', 23, True, 52, callback=iris.button_sender),
    Button('plus', 33, True, 53, callback=iris.button_sender),
    Button('off', 39, True, 54, callback=iris.button_sender)
    ]

async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(20)
        
    # -------------------------------------------------
    
def this_show(*args):
    lights = [red, yellow, green, blue, white, buzz]
    for light in lights:
        light.pin.on()
        utime.sleep_ms(500)
        light.pin.off()
        
    # -------------------------------------------------
    
this = {
    79: this_show,
    94: red.can_write,
    95: yellow.can_write,
    96: green.can_write,
    97: blue.can_write,
    98: white.can_write,
    99: buzz.can_write
    }
iris.things.update(this)