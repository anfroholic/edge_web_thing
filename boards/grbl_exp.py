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

def handle_encoders(msg):
    global theta_enc_val
    global phi_enc_val
    
    theta_enc_val, phi_enc_val = struct.unpack('ff', msg)
    print('angles', theta_enc_val, phi_enc_val)

import utime
def print_gen(gen):
    print(next(gen))
    for it in gen:
        print(it)
        utime.sleep_ms(30)

async def reset_axis(axis):
    if axis == 'x' or axis == 'y':
        resets[axis].off()
        await asyncio.sleep_ms(50)
        resets[axis].on()
    elif axis == 'xy':
        resets['x'].off()
        resets['y'].off()
        await asyncio.sleep_ms(50)
        resets['x'].on()
        resets['y'].on()

def offset2enc(axis):
    if axis == 'x':
        grbl.offset[axis] = grbl.status['MPos'][axis] - theta_enc_val 
    if axis == 'y':
        grbl.offset[axis] = grbl.status['MPos'][axis] - phi_enc_val


async def home_theta():
    await reset_axis('x')
    await asyncio.sleep_ms(500)
    offset2enc('x')
#     line = f'G1 X{theta_enc_val * -1} F500'
#     print(line)
    grbl.move({'x': 0})
    await asyncio.sleep_ms(5000)
    while True:
        if grbl.status['state'] == 'Idle':
            break
        await asyncio.sleep_ms(20)
    print('should be homed')

this = {
    68: handle_encoders,
    69: iris.can.callback,
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
    91: lambda m: grbl.load_script('test_prog.evzr'),
    92: lambda m: asyncio.get_event_loop().create_task(reset_axis('x')),
    93: lambda m: asyncio.get_event_loop().create_task(reset_axis('x')),
    94: lambda m: asyncio.get_event_loop().create_task(reset_axis('x'))
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
boards.webpage.grbl = grbl

boards.webpage.actions.update({
    '/unlock': grbl.unlock,
    '/sleep': grbl.sleep,
    '/wake': grbl.wake,
    '/homeZ': lambda: grbl.home('Z'),
    '/reset_x': lambda: asyncio.get_event_loop().create_task(reset_axis('x')),
    '/reset_y': lambda: asyncio.get_event_loop().create_task(reset_axis('y')),
    '/reset_xy': lambda: asyncio.get_event_loop().create_task(reset_axis('xy')),
    '/home_theta': lambda: asyncio.get_event_loop().create_task(home_theta())
    })

iris.can.subs[1752] = 68
iris.can.ignore.append(1752)
