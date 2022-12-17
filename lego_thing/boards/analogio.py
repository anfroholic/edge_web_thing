import config
from machine import DAC, Pin
import uasyncio as asyncio
from boards.utilities import *
import boards.iris as iris



#Setup LCD

output_1 = DigOUT('output_1', 19)
output_2 = DigOUT('output_2', 21)
output_3 = DigOUT('output_3', 22)
output_4 = DigOUT('output_4', 23)

hw = [
#     Analog('analog_1', 33, 62, callback=iris.button_sender),
#     Analog('analog_2', 32, 63, callback=iris.button_sender),
#     Analog('analog_3', 35, 64, callback=iris.button_sender),
#     Analog('analog_4', 34, 65, callback=iris.button_sender),
    Button('input_1', 25, True, 51, callback=iris.button_sender),
    Button('input_2', 26, True, 52, callback=iris.button_sender),
    Button('input_3', 18, True, 53, callback=iris.button_sender),
    Button('input_4', 27, True, 54, callback=iris.button_sender)
    ]

async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(20)
        
    # -------------------------------------------------
    
this = {
    88: lambda m: print('this'),
    91: output_1.can_write,
    92: output_2.can_write,
    93: output_3.can_write,
    94: output_4.can_write
    }
iris.things.update(this)