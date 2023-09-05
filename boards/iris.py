import machine
from boards.utilities import *
from config import config
import struct
import uasyncio as asyncio

broadcast_state = False
this_id = config['id']

bus = 'can'
if 'mqtt' in config:
    if config['mqtt']:
        bus = 'mqtt'
        print('mqtt enabled')
client = None

    # -------------------------------------------------

def fnc_chkr(event): # callback for fnc button
    print(event.state)
    global broadcast_state
    if not event.state:
        broadcast_state = not broadcast_state
        if broadcast_state:
            neo_status.fill(0, 12, 3)
        else:
            neo_status.fill(0, 0, 0)

    # -------------------------------------------------

can = CanMgr(0,
            tx=config['can_tx'],
            rx=config['can_rx'],
            extframe=True,
            mode=CAN.NORMAL,
            baudrate=250000,
            slp_pin=config['can_slp']
            )

def mqtt_begin():
    global client
    client = MqttMgr(
        client_id = config['board'],
        server = config['mqtt_server'],
        subs = ['#']
        )
    loop = asyncio.get_event_loop()
    loop.create_task(client.chk())
    

hbt_led = Pin(config['hbt'], Pin.OUT)
neo_status = NeoMgr(config['neo_status'], 1)
fnc_but = Button('fnc_button', 36, False, 99, callback=fnc_chkr)

    # -------------------------------------------------

async def do_hbt():
    while True:
        hbt_led.value(not hbt_led.value())
        await asyncio.sleep_ms(500)

    # -------------------------------------------------

def button_sender(event):
    print(f'{event.name}, {event.state}, id: {event.can_id}')
    if broadcast_state:
        if bus == 'can':
            can.send(struct.pack('b', event.state), event.can_id)
        elif bus == 'mqtt':
            if event.state:
                state = b'\x01'
            else:
                state = b'\x00'
            client.client.publish(str(event.can_id), state, qos=1)

    # -------------------------------------------------
    
def stater(state: str, pid: int):
    if broadcast_state:
        if bus == 'can':
            can.send(state.encode(), this_id + pid)


    # -------------------------------------------------
    
def set_b_state(msg):
    global broadcast_state
    broadcast_state = bool(struct.unpack('B', msg)[0])
    if broadcast_state:
        neo_status.fill(0, 12, 3)
    else:
        neo_status.fill(0, 0, 0)

    # -------------------------------------------------

async def fnc_chk():
    while True:
        fnc_but.chk()
        await asyncio.sleep_ms(50)

    # -------------------------------------------------

def process(hdr: int, msg: bytearray):
    
    if hdr < 100 or (hdr >= this_id and hdr <= (this_id+99)):
        things[hdr%100](msg)

    if hdr in can.subs:
        things[can.subs[hdr]%100](msg)
        
def add_sub(pub_pid, sub_pid):
    can.subs[pub_pid] = sub_pid
        
    # -------------------------------------------------

things = {
    1: neo_status.light_show,
    2: lambda m: machine.reset(),
    3: neo_status.can_fill,
    4: set_b_state,
    5: lambda m: can.send(config['board'].encode(), this_id+5), 
    48: can.clear_subs,
    49: can.create_sub
    }
