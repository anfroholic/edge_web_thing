import uasyncio as asyncio
from boards.utilities import *
import boards.iris as iris





fet_1 = DigOUT('fet_1', 19)
fet_2 = DigOUT('fet_2', 18)
fet_3 = DigOUT('fet_3', 25)
fet_4 = DigOUT('fet_4', 21)
fet_5 = DigOUT('fet_5', 22)
fet_6 = DigOUT('fet_6', 23)


hw = [
    ]

async def hw_chk():
    while True:
        pass
        await asyncio.sleep_ms(5000)

    # -------------------------------------------------

def this_show(*args):
    lights = [fet_1, fet_2, fet_3, fet_4, fet_5, fet_6]
    for light in lights:
        light.pin.on()
        utime.sleep_ms(500)
        light.pin.off()

    # -------------------------------------------------

this = {
    79: this_show,
    91: fet_1.can_write,
    92: fet_2.can_write,
    93: fet_3.can_write,
    94: fet_4.can_write,
    95: fet_5.can_write,
    96: fet_6.can_write
    }
iris.things.update(this)
