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
gc.collect()

neo_status = NeoMgr(17, 1)
neo_status.fill(0,5,5)
sta = wlan.connect()
neo_status.fill(0,0,0)
my_ip = sta.ifconfig()[0]

uart1 = UartMgr(1, baudrate=115200, rx=23, tx=22)
hbt = HBT(pin=5, interval=500)
can = CanMgr(0, tx=18, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000, slp_pin=19)
sd = SDMgr(slot=3)
sd.mount()

grbl = cnc.GRBL(sd, can, uart1, hbt_int=8000)

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

async def handle_client(reader, writer):
    request = (await reader.read(1024)).decode('ascii')
    page = None
    print(request)
    end = request.find(' HTTP')
    action = request[4:end]
    print(action)
    if action == '/cnc':
        web_page.page = 'cnc'
    elif action == '/home':
        web_page.page = None

    if action.find('/can') == 0:
        # can.send(**web_page.parse_can(action))
        print(web_page.parse_can(action))
    elif action.find('/sub') == 0:
        # can.create_sub(**web_page.parse_sub(action))
        print(web_page.parse_sub(action))
    elif action.find('/prog') == 0:
        can.create_prog(action)
    elif action == '/led=on':
        neo_status.fill(0, 25, 0)
    elif action == '/led=off':
        neo_status.fill(0, 0, 0)
    elif action == '/reset':
        can.connections = ''
        can.send([1], 2)
    elif action == '/light_show':
        can.send([1], 1)
    elif action == '/broadcast':
        can.send([1], 4)
    elif action == '/!broadcast':
        can.send([0], 4)
    elif action == '/demo1':
        demo1()
        
    elif action == '/?get_state':
        # print('getting state')
        grbl.uart.write('?')
    elif action == '/?unlock':
        print('unlocking')
        grbl.unlock()
    elif action == '/?sleep':
        print('putting to sleep')
        grbl.sleep()
    elif action == '/?wake_up':
        print('waking up grbl')
        grbl.wake()
    elif action == '/?run':
        print('run file')
        grbl.run()
        
    elif action == '/?homex':
        print('homing x')
        grbl.home('x')
    elif action == '/?homey':
        print('homing y')
        grbl.home('y')
    elif action == '/?homez':
        print('homing z')
        grbl.home('z')
    elif action == '/?homea':
        print('homing a')
        grbl.home('a')
    elif action == '/?homeb':
        print('homing b')
        grbl.home('b')    
    elif action == '/?homec':
        print('homing c')
        grbl.home('c')
    
    
    elif action == '/?ring_on':
        can.send([33,33,33], 397)
    elif action == '/?ring_off':
        can.send([0,0,0], 397)
    elif action == '/?suck_on':
        print('suction on')
        can.send([1], 399)
        print('message sent')
    elif action == '/?suck_off':
        can.send([0], 399)

    elif action == '/?spindle_on':
        can.send([1], 1492)
    elif action == '/?spindle_off':
        can.send([0], 1492)
    elif action == '/?vise_open':
        print('vise open')
        can.send([1], 1196)
        print('message sent')
    elif action == '/?vise_close':
        can.send([0], 1196)
    elif action == '/?coolant_on':
        print('vise open')
        can.send([1], 1195)
        print('message sent')
    elif action == '/?coolant_off':
        can.send([0], 1195)
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
        await writer.awrite(cnc.web_page())
    else:
        await writer.awrite(web_page.web_page(can.connections, sd.html_list))
    await writer.aclose()
    return True


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
