import wlan
from machine import Pin
import json
import utime
import machine
from utilities import *
import uasyncio as asyncio
import web_page
import cnc
import gc
import config
gc.collect()

pins = config.grbl_1_4

neo_status = NeoMgr(pins['neo_status'], 1)
neo_status.fill(0,5,5)
sta = wlan.connect()
neo_status.fill(0,0,0)
my_ip = sta.ifconfig()[0]


# detect = Pin(25, Pin.IN)
uart1 = UartMgr(1, baudrate=115200, rx=pins['uart_rx'], tx=pins['uart_tx'])
hbt = HBT(pin=pins['hbt'], interval=500)
can = CanMgr(0, tx=pins['can_tx'], rx=pins['can_rx'], extframe=True, mode=CAN.NORMAL, baudrate=250000, slp_pin=pins['can_slp'])
sd = SDMgr(slot=pins['sd_slot'])
try:
    sd.mount()
except OSError:
    print('sd failed to mount')
    pass
grbl = cnc.GRBL(sd, can, uart1, hbt_int=8000, debug=True, resets=True)

def print_state(state, button):
    print(state, button.can_id)
func_button = Button('func button', 36, False, 54, print_state)

async def chk_hw():
    while True:
        hbt.chk()
        func_button.chk()
        await asyncio.sleep_ms(50)

async def grblchk():
    while True:
        uart1.chk()
        grbl.chk()
        await asyncio.sleep_ms(10)

cmds = {
    '/led=on': lambda: neo_status.fill(0, 25, 0),
    '/led=off': lambda: neo_status.fill(0, 0, 0),
    '/light_show': lambda: can.send([1], 1),
    '/broadcast': lambda: can.send([1], 4),
    '/!broadcast': lambda: can.send([0], 4),
    '/demo1': lambda: demo1()
}

cmds.update(**grbl.web_buts())


async def handle_client(reader, writer):
    request = (await reader.read(1024)).decode('ascii')
    page = None
    # print(request)
    end = request.find(' HTTP')
    action = request[4:end]
    print(action)
    if action == '/cnc':
        web_page.page = 'cnc'
    elif action == '/home':
        web_page.page = None

    if action in cmds:
        cmds[action]()
    elif action.find('/move') == 0:
        grbl.parse_move(request)

    elif action.find('/offset') == 0:
        grbl.set_offset(request)
    elif action.find('/can') == 0:
        # can.send(**web_page.parse_can(action))
        print(web_page.parse_can(action))
    elif action.find('/sub') == 0:
        # can.create_sub(**web_page.parse_sub(action))
        print(web_page.parse_sub(action))
    elif action.find('/prog') == 0:
        can.create_prog(action)
    elif action == '/reset':
        can.connections = ''
        can.send([1], 2)
    elif action == '/?run_export':
        print('run export file')
        sd.opener('t.txt')
        grbl.run()
    elif action.find('/file') == 0:
        name = action.split('=')[1]
        print('opening file {}'.format(name))
        sd.opener(name)
    elif action.find('/direct') == 0:
        fn = action.split('=')
        action = fn[1].replace('+', ' ')
        print('sending direct ' + action)
        grbl.send_g(action)
    elif action.find('/feeder') == 0:
        fn = action.split('=')
        print(fn)

    else:
        print('unknown command')

    await writer.awrite(
        b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
    if web_page.page == 'cnc':
        await writer.awrite(grbl.web_page())
    else:
        await writer.awrite(web_page.web_page(can.connections, sd.html_list))
    await writer.aclose()
    return True

test_move = [
{'cmd': 'move.linear', 'x':1000, 'feed':10000},
{'cmd': 'move.linear', 'x':0, 'feed':10000},
None
]
grbl.buf = test_move

gc.collect()
print(gc.mem_free())
async def main():
    asyncio.create_task(asyncio.start_server(handle_client, my_ip, 80))
    asyncio.create_task(chk_hw())
    asyncio.create_task(can.chk())
    asyncio.create_task(grblchk())
    while True:
        await asyncio.sleep(5)

gc.collect()
while True:
    asyncio.run(main())
