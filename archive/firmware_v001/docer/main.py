
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
    for i in range(20):
        lcd.scroll(0,2)
        lcd.show()
        utime.sleep_ms(30)

    for i in range(20):
        lcd.scroll(0,-2)
        lcd.show()
        utime.sleep_ms(30)


