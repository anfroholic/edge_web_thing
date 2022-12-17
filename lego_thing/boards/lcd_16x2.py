import boards.lcd_api
import boards.lcd_driver
import config
from machine import DAC, Pin
import uasyncio as asyncio
from boards.utilities import *
import boards.iris as iris



#Setup LCD


hw = [
    Button('a_button', 39, False, 50, callback=iris.button_sender),
    Button('b_button', 34, False, 51, callback=iris.button_sender),
    Button('down_button', 35, False, 53, callback=iris.button_sender),
    Button('up_button', 33, True, 52, callback=iris.button_sender),
    Button('left_button', 26, True, 54, callback=iris.button_sender),
    Button('right_button', 32, True, 55, callback=iris.button_sender)    
    ]

async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(20)
        
    # -------------------------------------------------
    
class LCD:
    def __init__(self):
        self.text = [['',''], ['','']]
        self.lcd = boards.lcd_driver.GpioLcd(rs_pin=27,
                  enable_pin=14,
                  d0_pin=12,
                  d1_pin=13,
                  d2_pin=15,
                  d3_pin=18,
                  d4_pin=19,
                  d5_pin=21,
                  d6_pin=22,
                  d7_pin=23,
                  num_lines=2, num_columns=16)
        self.lcd.putstr('16x2 LCD LOADED')

    # -------------------------------------------------

    async def chk(self):
        while True:    
            await asyncio.sleep_ms(5000)
            self.update()

    # -------------------------------------------------

    def update(self):
        self.lcd.move_to(0,0)
        line = ''.join(self.text[0])[:16]
        self.lcd.putstr(f'{line:<16}')

        self.lcd.move_to(0,1)
        line = ''.join(self.text[1])[:16]
        self.lcd.putstr(f'{line:<16}')
        
    # -------------------------------------------------
    
    def set_str(self, msg: bytearray, index: int):
        line = struct.unpack(f'{len(msg)}s', msg)[0].decode('utf8')
        if index == 0:
            self.text[0][0] = line
        elif index == 1:
            self.text[0][1] = line
        elif index == 2:
            self.text[1][0] = line
        elif index == 3:
            self.text[1][1] = line
        else:
            print('index out of range')
            raise IndexError
        self.update()
        
    # -------------------------------------------------
    
    def set_byte(self, msg: bytearray, index: int):
        line = str(struct.unpack('B', msg)[0])
        if index == 0:
            self.text[0][0] = line
        elif index == 1:
            self.text[0][1] = line
        elif index == 2:
            self.text[1][0] = line
        elif index == 3:
            self.text[1][1] = line
        else:
            print('index out of range')
            raise IndexError
        self.update()
        
    # -------------------------------------------------
    
    def set_buf(self, msg: bytearray, index: int):
        line = str(msg)
        if index == 0:
            self.text[0][0] = line
        elif index == 1:
            self.text[1][0] = line
        else:
            print('index out of range')
            raise IndexError
        self.update()
        
    # -------------------------------------------------
    
    def clear(self, *args):
        self.text = [['',''], ['','']]
        self.update()


lcd = LCD()

this = {
    88: lambda m: lcd.set_buf(m, 0),
    89: lambda m: lcd.set_buf(m, 1),
    90: lambda m: lcd.set_str(m, 0),
    91: lambda m: lcd.set_str(m, 1),
    92: lambda m: lcd.set_str(m, 2),
    93: lambda m: lcd.set_str(m, 3),
    95: lambda m: lcd.set_byte(m, 0),
    96: lambda m: lcd.set_byte(m, 1),
    97: lambda m: lcd.set_byte(m, 2),
    98: lambda m: lcd.set_byte(m, 3),
    99: lcd.clear
    }
iris.things.update(this)

loop = asyncio.get_event_loop()
loop.create_task(lcd.chk())