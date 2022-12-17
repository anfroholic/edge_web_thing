import utime
from machine import Pin, CAN, ADC
import machine
import config
import uasyncio as asyncio
from utilities import *

machine.freq(240000000)
import gc
gc.collect()

can = CanMgr(0,
            tx=config.config['can_tx'],
            rx=config.config['can_rx'],
            extframe=True,
            mode=CAN.NORMAL,
            baudrate=250000,
            slp_pin=config.config['can_slp']
            )




hbt_led = Pin(5, Pin.OUT)

async def do_hbt():
    while True:
        hbt_led.value(not hbt_led.value())
        await asyncio.sleep_ms(500)



_board = __import__('boards.' + config.config['board'])
board = getattr(_board, config.config['board'])







loop = asyncio.get_event_loop()

loop.create_task(do_hbt())
loop.create_task(can.chk())

loop.run_forever()