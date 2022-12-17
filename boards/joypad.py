import boards.iris as iris
import machine
from boards.utilities import *
import uasyncio as asyncio



print('joypad 1.2 imported')


neo_bar = NeoMgr(12, 5)

hw = [
Button('green_button', 25, True, 50, callback=iris.button_sender),
Button('red_button', 26, True, 51, callback=iris.button_sender),
Button('blue_button', 27, True, 52, callback=iris.button_sender),
Button('yellow_button', 33, True, 53, callback=iris.button_sender),
Button('start_button', 13, True, 54, callback=iris.button_sender),
Button('select_button', 15, True, 55, callback=iris.button_sender),
Button('up_button', 21, True, 56, callback=iris.button_sender),
Button('down_button', 23, True, 57, callback=iris.button_sender),
Button('left_button', 19, True, 58, callback=iris.button_sender),
Button('right_button', 22, True, 59, callback=iris.button_sender),
Button('l_joy_push', 18, True, 60, callback=iris.button_sender),
Button('r_joy_push', 14, True, 61, callback=iris.button_sender),
Analog('L_X', 35, 62, callback=iris.button_sender),
Analog('L_Y', 32, 63, callback=iris.button_sender),
Analog('R_X', 34, 64, callback=iris.button_sender),
Analog('R_Y', 39, 65, callback=iris.button_sender)
    ]

async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(30)

this = {
    94: neo_bar.light_show,
    95: neo_bar.can_fill
    }
iris.things.update(this)

