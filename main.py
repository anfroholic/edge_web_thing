

import usocket as socket
import utime
from machine import Pin
import network
import urequests as requests
from neopixel import NeoPixel
import esp
esp.osdebug(None)
import uasyncio

import gc
gc.collect()

ssid = 'Grammys_IoT'
password = 'AAGI96475'


station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while not sta_if.isconnected():
    print(".", end = "")

print('Connection successful')
print(station.ifconfig())


# set up pins
hbt_led = Pin(5, Pin.OUT)
neo_status_pin = Pin(17, Pin.OUT)
neo_status = NeoPixel(neo_status_pin, 1)
func_button = Pin(36, Pin.IN) # Has external pullup
json_loaded = 'None'




def web_page():
  global json_loaded
  if hbt_led.value() == 1:
      gpio_state="Active"
  else:
      gpio_state="Disconnected"


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

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

def handle_socket():
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    request = str(request)
    # print('Content = %s' % request)
    led_on = request.find('/?led=on')
    led_off = request.find('/?led=off')
    load_json = request.find('/?load_json')

    if led_on == 6:
        print('LED ON')
        neo_status[0] = (0, 33, 0)
        neo_status.write()
    if led_off == 6:
        print('LED OFF')
        neo_status[0] = (0, 0, 0)
        neo_status.write()
    if load_json == 6:
        print('load json')
        json_loaded = 'Would be nice if this were built'
    response = web_page()
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    conn.close()


while True:
    if not func_button.value():
        print('function button pressed')
        utime.sleep(250)
    handle_socket()
    chk_hbt()
