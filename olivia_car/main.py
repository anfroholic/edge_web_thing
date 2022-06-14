from machine import Pin, PWM
from utilities import *
import utime


def do_move(state, button):
    move_time = 1500
    if state:
        print('forward')
        forward()
        utime.sleep_ms(move_time)
        print('reverse')
        reverse()
        utime.sleep_ms(move_time)
        print('right')
        right()
        utime.sleep_ms(move_time)
        print('left')
        left()
        utime.sleep_ms(move_time)
        print('done')
        stop()

m_l1 = PWM(Pin(14), freq=10000, duty=0)
m_l2 = PWM(Pin(26), freq=10000, duty=0)
m_r1 = PWM(Pin(25), freq=10000, duty=0)
m_r2 = PWM(Pin(33), freq=10000, duty=0)

utime.sleep_ms(10)
m_l1.duty(0)
m_l2.duty(0)
m_r1.duty(0)
m_r2.duty(0)

func_button = Button('func button', 36, False, 54, do_move)
neo_bar = NeoMgr(15, 5)
hbt = HBT(pin=27, interval=500)
neo_status = NeoMgr(12, 1)

def forward():
    m_l1.duty(700)
    m_r1.duty(700)
    m_l2.duty(0)
    m_r2.duty(0)


def stop():
    m_l1.duty(0)
    m_l2.duty(0)
    m_r1.duty(0)
    m_r2.duty(0)
    
def reverse():
    m_l1.duty(0)
    m_r1.duty(0)
    m_l2.duty(700)
    m_r2.duty(700)

def right():
    m_l1.duty(700)
    m_l2.duty(0)
    m_r2.duty(700)
    m_r1.duty(0)

def left():
    m_l1.duty(0)
    m_l2.duty(700)
    m_r1.duty(700)
    m_r2.duty(0)

 
def main():
    while True:
        hbt.chk()
        neo_bar.chk()
        func_button.chk()
        utime.sleep_ms(40)

neo_status.light_show()
main()