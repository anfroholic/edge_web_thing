from machine import Pin, CAN
import utime


f_but = Pin(36, Pin.IN)

can_slp = Pin(2, Pin.OUT, value=0)
can_slp.value(0)

can = CAN(0, tx=4, rx=16, extframe=True, mode=CAN.NORMAL, baudrate=250000)

def led(arg: int):
    can.send([arg], 2359317)

def neo_status(arg: bytes):
    can.send(arg, 2360157)


def nibble(arg):
    can.send(list(arg), 2359499)

def big(arg):
    buf = arg.encode() + b'\x04'
    while True:
        if buf:
            if len(buf) > 8:
                can.send(list(buf[:8]), 2359501)
                buf = buf[8:]
            else:
                can.send(list(buf), 2359501)
                break
        utime.sleep_ms(2)

print('loaded')



def main():
    while True:
        if can.any():
            h, x, y, b = can.recv()
            print(h,b)
        if not f_but.value():
            print('exiting')
            break
