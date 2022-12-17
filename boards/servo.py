import config
from machine import DAC, Pin
import uasyncio as asyncio
from boards.utilities import *
import boards.iris as iris



#Setup LCD

servo_1 = Servo(26)
servo_2 = Servo(27)
servo_3 = Servo(25)
servo_4 = Servo(14)
servo_6 = Servo(12)
servo_8 = Servo(18)
servo_10 = Servo(19)
servo_12 = Servo(21)

def all_servos(pos):
    servos = [servo_1, servo_2, servo_3, servo_4, servo_6, servo_8, servo_10, servo_12]
    for servo in servos:
        servo.set(pos)


hw = [
    Button('button_a', 22, True, 50, callback=iris.button_sender),
    Button('button_b', 23, True, 51, callback=iris.button_sender)
    ]

async def hw_chk():
    while True:
        for h in hw:
            h.chk()
        await asyncio.sleep_ms(20)

    # -------------------------------------------------

this = {
    88: lambda m: print('this'),
    91: servo_1.set,
    92: servo_2.set,
    93: servo_3.set,
    94: servo_4.set,
    95: servo_6.set,
    96: servo_8.set,
    97: servo_10.set,
    98: servo_12.set,
    99: all_servos
    }
iris.things.update(this)
