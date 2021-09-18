


from gcode_conversion import *  #asyncio does not seem to be able to make outside calls from within handle_client


import utime
from machine import Pin
import machine
import network
from neopixel import NeoPixel
import esp
esp.osdebug(None)
import uasyncio as asyncio

import gc
gc.collect()

ssid = 'Grammys_IoT'
password = 'AAGI96475'
port = 80
loop = asyncio.get_event_loop()


# set up pins
hbt_led = Pin(5, Pin.OUT)
neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
func_button = Pin(36, Pin.IN) # Has external pullup


#network
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

neo_status[0] = (10, 0, 0)
neo_status.write()
while not station.isconnected():
    print(".", end = "")
    utime.sleep_ms(250)

print('Connection successful')
print(station.ifconfig())
my_ip = station.ifconfig()[0]
neo_status[0] = (0, 10, 0)
neo_status.write()
utime.sleep_ms(250)
neo_status[0] = (0, 0, 0)
neo_status.write()


def web_page():
  connect_state = 'fix connection'

  html = """
<html>
    <head>
        <title>Evezor Web Interface</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
  h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
  border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  .button2{background-color: #4286f4;}.button3{background-color: #06876f;}</style>
    </head>
    <body>
    <h1>Evezor Web Interface</h1>
    <p>Connection State: <strong>""" + connect_state + """</strong></p>

    <p><a href="/?led=off"><button class="button button2">neo off</button></a>          <a href="/?led=on"><button class="button">neo on</button></a></p>

    <p><a href="/?load_json"><button class="button button3">unused</button></a></p>
    <br><br>
    <p><strong>Move Machine</strong></p>

    <form action="/move.php">
    <label for="send_x">X:</label>
    <input type="text" id="x" name="x"><br><br>
    <label for="send_y">Y:</label>
    <input type="text" id="y" name="y"><br><br>
    <label for="send_z">Z:</label>
    <input type="text" id="z" name="z"><br><br>
    <label for="send_a">A:</label>
    <input type="text" id="a" name="a"><br><br>
    <input type="submit" value="Submit">
    </form>
    </body></html>"""
  return html

def parse_move(request):
    end = request.find(' HTTP')
    action = request[14:end]
    action += '&'
    # print('parsing request')
    # print(action)
    axes = ['x', 'y', 'z', 'a']
    parsed = {}
    for axis in axes:
        index = action.find('&')
        if action[2: index] != '':
            parsed[axis] = action[2: index]
        action = action[(index + 1):]
    # print(parsed)
    parsed['command'] = 'move.linear'
    parsed['feed'] = 2000
    return parsed


async def buttons():
    while True:
        if not func_button.value():
            print('function button pressed')
            await asyncio.sleep_ms(250)
        await asyncio.sleep_ms(50)

async def do_hbt():
    while True:
        hbt_led.value(1)
        await asyncio.sleep(.1)
        hbt_led.value(0)
        await asyncio.sleep(.9)

async def handle_client(reader, writer):
    request = (await reader.read(1024)).decode('ascii')
    print(request)

    # process request
    if request.find('/move') == 4:
        parsed = parse_move(request)
        # print(parsed)
        print(convert(**parsed))

    if request.find('/?led=on') == 4:
        print('turn led on')
        neo_status[0] = (0, 25, 0)
        neo_status.write()
    if request.find('/?led=off') == 4:
        print('turn led off')
        neo_status[0] = (0, 0, 0)
        neo_status.write()

    await writer.awrite(
        b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
    # with open(web_page(), 'rb') as response:
    #     while True:
    #         buf = response.read(1024)
    #         if len(buf):
    #             await writer.awrite(buf)
    #         if len(buf) < 1024:
    #             break
    await writer.awrite(web_page())
    await writer.aclose()
    return True


async def main():
    asyncio.create_task(asyncio.start_server(handle_client, my_ip, port))
    asyncio.create_task(do_hbt())
    asyncio.create_task(buttons())
    while True:
        await asyncio.sleep(5)


while True:
    asyncio.run(main())
