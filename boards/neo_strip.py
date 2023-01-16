import boards.iris as iris
import machine
from boards.utilities import *
import uasyncio as asyncio



print('neo_strip v1.0 imported')


neo_a = NeoMgr(23, 5)
neo_b = NeoMgr(22, 5)

hw = [
Button('a_button', 21, True, 50, callback=iris.button_sender),
Button('b_button', 19, True, 51, callback=iris.button_sender),
Button('c_button', 15, True, 52, callback=iris.button_sender)
    ]

async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(30)

this = {
    91: neo_a.light_show,
    92: neo_a.can_fill,
    93: neo_a.light_show,
    94: neo_a.can_fill
    }
iris.things.update(this)