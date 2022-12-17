
import wlan
from wlan import API
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
api = API(host='10.203.136.47', port=8000, my_ip=my_ip)

def print_state(state, button):
    print(state, button.can_id)

def get_time(state, button):
    if state:
        print(state, button.can_id)
        api.get_queue.append('time')

def make_post(state, button):
    if state:
        print(state, button.can_id)
        api.post_queue.append(('create_test_message', '{"sparta": 42069, "this": "is"}'))

def this_show(state, button):
    if state:
        leds = [led_a, led_b, led_c, led_d]
        for i in range(4):
            for led in leds:
                led.on()
                utime.sleep_ms(50)
            utime.sleep_ms(300)
            for led in leds:
                led.off()

def bus_show(state, button):
    if state:
        neo_bus.light_show()


button_a = Button('button a', 34, False, 50, get_time)
button_b = Button('button b', 26, True, 51, make_post)
button_c = Button('button c', 14, True, 52, this_show)
button_d = Button('button d', 12, True, 53, bus_show)
func_button = Button('func button', 36, False, 54, print_state)

led_a = Pin(33, Pin.OUT, value=0)
led_b = Pin(25, Pin.OUT, value=0)
led_c = Pin(21, Pin.OUT, value=0)
led_d = Pin(22, Pin.OUT, value=0)

hbt = HBT(pin=15, interval=500)
neo_bus = NeoMgr(27, 2)

can = CanMgr(0, tx=4, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000, slp_pin=2)
sd = SDMgr(slot=2)
sd.mount()


def demo_1():
    global connections
    neo_status.fill(0, 0, 20)
    if can.connections == '':
        for sub in test_prog1:
            can.make_sub(sub[0], sub[1])
            utime.sleep_ms(25)
        # TODO: make the words show on lcd here
        utime.sleep_ms(25)
        can.send([1], 4) #  broadcast
        utime.sleep_ms(25)
        can.send(list(b'TEMP: '), 791) # TEMP:
        utime.sleep_ms(25)
        can.send(list(b'WEIGHT: '), 793) # WEIGHT:
    neo_status.fill(0, 0, 0)


async def chk_hw():
    while True:
        hbt.chk()
        button_a.chk()
        button_b.chk()
        button_c.chk()
        button_d.chk()
        func_button.chk()
        neo_bus.chk()
        await asyncio.sleep_ms(50)


async def handle_socket(reader, writer):
    request = (await reader.read(1024)).decode('ascii')
    print(request)

    await writer.awrite(
        b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
    # await writer.awrite(web_page())
    await writer.aclose()
    return True

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
    asyncio.create_task(asyncio.start_server(handle_socket, my_ip, 8000))
    asyncio.create_task(chk_hw())
    asyncio.create_task(api.chk())
    asyncio.create_task(can.chk())
    while True:
        await asyncio.sleep(5)

gc.collect()
while True:
    asyncio.run(main())
