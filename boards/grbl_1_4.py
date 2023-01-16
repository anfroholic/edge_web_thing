import config
from boards.utilities import *
import boards.iris as iris
import struct
from boards.grbl import GRBL

uart = uart1 = UartMgr(1, baudrate=115200, rx=23, tx=22)

grbl = GRBL(can=iris.can, uart=uart, axes = ['x','y','z'], hbt_int=5000)


async def hw_chk():
    while True:
        uart.chk()
        grbl.chk()
        await asyncio.sleep_ms(1)

    # -------------------------------------------------


test_prog = [
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500},
    {'cmd': 'move.linear', 'x':10, 'feed': 500},
    {'cmd': 'move.linear', 'x':0, 'feed': 500}
    ]


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
