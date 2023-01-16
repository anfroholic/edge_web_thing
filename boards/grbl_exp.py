import config
from boards.utilities import *
import boards.iris as iris
import struct
from machines.grbl import GRBL
from machine import Pin

uart = uart1 = UartMgr(1, baudrate=115200, rx=14, tx=21)

grbl = GRBL(can=iris.can, uart=uart, axes = ['x','y','z'], hbt_int=5000)

reset_pins = {"x":25, "y":26, "z":27}

    
resets = {axis: Pin(pin, Pin.OUT) for axis, pin in reset_pins.items()}

for pin in resets.values():
    pin.on()

async def hw_chk():
    while True:
        uart.chk()
        grbl.chk()
        await asyncio.sleep_ms(20)

    # -------------------------------------------------

import utime
def print_gen(gen):
    print(next(gen))
    for it in gen:
        print(it)
        utime.sleep_ms(75)
        


#  if struct.unpack('?', m)[0]

this = {
    80: grbl.unlock,
    81: grbl.sleep,
    82: grbl.wake,
    83: lambda m: grbl.home('x') if bool(struct.unpack('b', m)[0]) else print('no homex'),
    84: lambda m: grbl.home('y') if bool(struct.unpack('b', m)[0]) else print('no homey'),
    85: lambda m: grbl.home('z') if bool(struct.unpack('b', m)[0]) else print('no homez'),
    86: grbl.movex,
    87: grbl.movey,
    88: grbl.movez,
    89: grbl.set_hbt,
    90: lambda m: grbl.load_script(test_prog),
    91: lambda m: grbl.load_script('test_prog.evzr')
    }

iris.things.update(this)

import boards.webpage


# set up PNP
import machines.pnp


pnp = machines.pnp.PNP(**machines.pnp.config)

def run_pnp_script(script):
    print('run', script)
    print_gen(pnp.create_gen({'x': 295.5, 'y': 307.2, 'z': 0}, pos_file=script))
    # grbl.load_script(pnp.create_gen({'x': 295.5, 'y': 307.2, 'z': 0}, pos_file=script))

boards.webpage.cnc_callback = run_pnp_script


