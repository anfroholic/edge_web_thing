

# import usocket as socket
import utime
from machine import Pin
import network
# import urequests as requests
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

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while not station.isconnected():
    print(".", end = "")
    utime.sleep_ms(250)

print('Connection successful')
print(station.ifconfig())
my_ip = station.ifconfig()[0]

# set up pins
hbt_led = Pin(5, Pin.OUT)
neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
func_button = Pin(36, Pin.IN) # Has external pullup





def web_page():
  gpio_state = 'some gpio state'
  json_loaded = 'some json'
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
    <p>BUS state: <strong>""" + gpio_state + """</strong></p><p><a href="/?led=on"><button class="button">CONNECT</button></a></p>
    <p><a href="/?led=off"><button class="button button2">DISCONNECT</button></a></p>
    <p>Map File = <strong>""" + json_loaded + """</strong></p>
    <p><a href="/?load_json"><button class="button button3">LOAD</button></a></p>
    </body></html>"""
  return html

async def time_check():
        # do the time check etc here
        print('Bar started: waiting {}secs')
        await asyncio.sleep(.1)


async def handle_client(reader, writer):
    request = (await reader.read(1024)).decode('utf8')
    print(request)
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

loop.create_task(asyncio.start_server(handle_client, my_ip, port))
# asyncio.create_task(asyncio.start_server(handle_client, my_ip, port))

# loop.create_task(time_check())
asyncio.run(time_check())
print('Time check and async webserver created, listening on {}:{}'.format(my_ip, port))
loop.run_forever()
