import uasyncio as asyncio
from boards.utilities import *
import boards.iris as iris
from boards.as5048b_encoder import Encoder
from machine import I2C, Pin

i2c = I2C(0, scl=Pin(23), sda=Pin(22), freq=400000)

theta_coder = Encoder(name='theta_coder', address=67, invert=True, offset=3076, i2c=i2c)
phi_coder = Encoder(name='phi_coder', address=64, invert=True, offset=3177, i2c=i2c)
theta_ring = NeoMgr(pin=21, num_pix=12)
phi_ring = NeoMgr(pin=13, num_pix=12)

hbt_int = 5

hw = [
    Button('button_a', 23, True, 50, callback=iris.button_sender),
    Button('button_b', 22, True, 51, callback=iris.button_sender),
    theta_ring,
    phi_ring,
    theta_coder,
    phi_coder
]


async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(20)

    # -------------------------------------------------

async def post_angles():
    while True:
        # print(theta_coder.angle, phi_coder.angle)
        print(f'theta: {theta_coder.angle}, phi: {phi_coder.angle}')
        await asyncio.sleep_ms(100)

def set_hbt(msg):
    global hbt_int
    hbt_int = struct.unpack('B', msg)[0] * 100

    # -------------------------------------------------


this = {
    92: set_hbt,
}
iris.things.update(this)


# Boot Sequence
while True:
    """make sure i2c devices are present"""
    found = True
    connected = i2c.scan()
    print(connected)
    if phi_coder.address not in connected:
        found = False
    if theta_coder.address not in connected:
        found = False
    if found:
        print('encoders present')
        break
    print('no encoder found')
    utime.sleep_ms(500)