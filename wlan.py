import webrepl
import network
import utime
import socket
import json
import uasyncio as asyncio

networks = {'evezor': 'drinkmaker', 'Grammys_IoT':'AAGI96475', 'Herrmann': 'storage18', 'PumpingStationOne': 'ps1frocks'}

def connect(neo: NeoStatus):
    neo.fill(0, 20, 20)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    aps = wlan.scan()
    print(aps)
    for ap in aps:
        net = ap[0].decode('ascii')
        if net in networks:
            print('connecting')
            wlan.connect(net, networks[net])
            
    
    
    timeout = utime.ticks_add(utime.ticks_ms(), 5000)
    while not wlan.isconnected():
        if utime.ticks_diff(timeout, utime.ticks_ms()) <= 0:
            print('wlan  connect failed')
            

        print(".", end = "")
        utime.sleep_ms(250)
    print('Connection successful')
    print(wlan.ifconfig()) 
    # webrepl.start()
    return wlan



class API:
    def __init__(self, *, host, port, my_ip):
        self.host = host
        self.port = port
        self.my_ip = my_ip
        self.get_queue = []
        self.post_queue = []

    async def check(self):
        while True:
            if self.get_queue:
                await self.get(self.get_queue.pop(0))
            if self.post_queue:
                post, mess = self.post_queue.pop(0)
                await self.post(post, mess)
            await asyncio.sleep_ms(10)

    async def get(self, path):

        reader, writer = await asyncio.open_connection(self.host, self.port)
        
        writer.write(bytes(
            'GET /{} HTTP/1.0\r\nHost: {}\r\n\r\n'.format(path, self.my_ip), 'utf8'))
        await writer.drain()
        
        data = (await reader.read(1024)).decode('ascii')
        print(data)
        writer.close()
        await writer.wait_closed()

    async def post(self, path, mess):
        c_len = len(mess)
        reader, writer = await asyncio.open_connection(self.host, self.port)
        
        writer.write(bytes(
            'POST /{} HTTP/1.0\r\nFrom: anfro@here.com\r\nUser-Agent: HTTPTool/1.0\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}'.format(path, c_len, mess), 'utf8'))
        await writer.drain()
        
        data = (await reader.read(1024)).decode('ascii')
        print(data)
        writer.close()
        await writer.wait_closed()

    

