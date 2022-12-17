
from machine import Pin, SoftI2C
import ssd1306
import utime

i2c = SoftI2C(scl=Pin(22), sda=Pin(23), freq=400000)
print('lcd test')

lcd = ssd1306.SSD1306_I2C(width=128, height=64, i2c=i2c, addr=0x3c, external_vcc=False)

utime.sleep_ms(1000)

lcd.text('Mechanical', 25, 2)
lcd.text('Mustache', 29, 15)
lcd.show()
utime.sleep_ms(50)

while True:
    for i in range(40):
        lcd.scroll(0,1)
        lcd.show()
        utime.sleep_ms(20)

    for i in range(40):
        lcd.scroll(0,-1)
        lcd.show()
        utime.sleep_ms(20)


