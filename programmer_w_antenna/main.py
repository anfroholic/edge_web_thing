


import utime
from machine import Pin, CAN, ADC
import machine
import network
from neopixel import NeoPixel
import esp
esp.osdebug(None)
import uasyncio as asyncio
import struct

import gc
gc.collect()

print('programmer board with antenna')
print('v1.00p')
print('initializing')

port = 80

networks = {'Grammys_IoT':'AAGI96475', 'Herrmann': 'storage18', 'PumpingStationOne': 'ps1frocks'}


can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000)

buf = bytearray(8)
mess = [0, 0, 0, memoryview(buf)]

# set up pins
hbt_led = Pin(5, Pin.OUT)
neo_status_pin = Pin(32, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
func_button = Pin(35, Pin.IN) # Has external pullup

neo_status[0] = (10, 0, 0)
neo_status.write()

can_slp = Pin(17, Pin.OUT, value=0)
can_slp.value(0)

#network
if func_button.value():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    aps = wlan.scan()

    neo_status[0] = (0, 10, 0)
    neo_status.write()


    for i in range(len(aps)):
        station = aps[i][0].decode('ascii')
        if station in networks:
            print('connecting to ' + station + ', '+ networks[station])
            wlan.connect(station, networks[station])

    neo_status[0] = (0, 0, 10)
    neo_status.write()

    while not wlan.isconnected():
        print(".", end = "")
        utime.sleep_ms(250)

    print('Connection successful')
    print(wlan.ifconfig())

    my_ip = wlan.ifconfig()[0]
    neo_status[0] = (0, 10, 0)
    neo_status.write()
    utime.sleep_ms(250)
    neo_status[0] = (0, 0, 0)
    neo_status.write()

else:
    neo_status[0] = (10, 0, 10)
    neo_status.write()
    print('function button pressed, becomming access point')
    wlan = network.WLAN(network.AP_IF) # create access-point interface
    wlan.config(essid='evezor') # set the ESSID of the access point
    wlan.config(max_clients=10) # set how many clients can connect to the network
    wlan.active(True)         # activate the interface
    my_ip = wlan.ifconfig()[0]

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

    <p>
    <a href="/?reset"><button class="button button3">reset</button></a>
    <a href="/?light_show"><button class="button button3">light show</button></a>
    <a href="/?broadcast"><button class="button button3">broadcast</button></a>
    <a href="/?!broadcast"><button class="button button3">!broadcast</button></a>
    </p>
    <br><br>
    <p><strong>Send CAN Message</strong></p>

    <form action="/can.php">
    <label for="send_arb">ARB:</label>
    <input type="text" id="send_arb" name="send_arb"><br><br>
    <label for="m0">m0:</label>
    <input type="text" id="m0" name="m0"><br>

    <label for="m1">m1:</label>
    <input type="text" id="m1" name="m1"><br>

    <label for="m2">m2:</label>
    <input type="text" id="m2" name="m2"><br>


    <label for="m3">m3:</label>
    <input type="text" id="m3" name="m3"><br>


    <label for="m4">m4:</label>
    <input type="text" id="m4" name="m4"><br>


    <label for="m5">m5:</label>
    <input type="text" id="m5" name="m5"><br>


    <label for="m6">m6:</label>
    <input type="text" id="m6" name="m6"><br>


    <label for="m7">m7:</label>
    <input type="text" id="m7" name="m7"><br>
    <input type="submit" value="Submit">
    </form>
    <br><br>
    <p><strong>Send CAN Message</strong></p>

    <form action="/sub.php">
    <label for="sub_num">Subscriber #:</label>
    <input type="text" id="sub_num" name="sub_num"><br><br>

    <label for="send_id">send ID:</label>
    <input type="text" id="send_id" name="send_id"><br><br>

    <label for="recv_id">recv ID:</label>
    <input type="text" id="recv_id" name="recv_id"><br><br>

    <input type="submit" value="Submit">
    </form>
    </body></html>"""
  return html

async def get_can():
    while True:
        if can.any():
            can.recv(mess)
            print(str(mess[0]) + ', ' + str(buf[0]))
        await asyncio.sleep_ms(1)

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

def send_can(request):
    end = request.find(' HTTP')
    action = request[13:end]
    action += '&'
    print(action)
    _mess = []
    for i in range(9):
        if action.find('&') - action.find('=') > 1:
            _mess.append(action[action.find('=')+1:action.find('&')])
            action = action[action.find('&')+1:]
    arb_id = int(_mess.pop(0))
    for i in range(len(_mess)): #convert to ints
        _mess[i] = int(_mess[i])
    print('sending')
    print(arb_id)
    print(_mess)
    can.send(_mess, arb_id)

def make_sub(request):
    end = request.find(' HTTP')
    action = request[13:end]
    print(action)
    sub = action.split('&')
    _sub = []
    for i in range(3):
        _sub.append(sub[i].split('=')[1])
    _mess = struct.pack('II', int(_sub[1]), int(_sub[2]))
    beer = []
    for i in range(len(_mess)):
        beer.append(int(_mess[i]))
    can.send(beer, (int(_sub[0])+49))

async def handle_client(reader, writer):
    request = (await reader.read(1024)).decode('ascii')
    # print(request)
    end = request.find(' HTTP')
    action = request[4:end]
    print(action)
    # process request
    if request.find('/can') == 4:
        send_can(request)
    if request.find('/sub') == 4:
        make_sub(request)

    elif action == '/?led=on':
        print('turn led on')
        neo_status[0] = (0, 25, 0)
        neo_status.write()
    elif action == '/?led=off':
        print('turn led off')
        neo_status[0] = (0, 0, 0)
        neo_status.write()
    elif action == '/?reset':
        can.send([1], 2)
    elif action == '/?light_show':
        can.send([1], 1)
    elif action == '/?broadcast':
        can.send([1], 4)
    elif action == '/?!broadcast':
        can.send([0], 4)

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
    asyncio.create_task(get_can())
    while True:
        await asyncio.sleep(5)


while True:
    asyncio.run(main())
