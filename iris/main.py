print('loading')
import json
import parameters
import esp32_driver
import gc
gc.collect()
import utime

from iris import Iris
import machine

machine.freq(240000000)

def add_param(d):
    iris.p[d['id']] = params[d['p_type']](iris=iris, **d)


def parse(**d):
    if 'sub_params' in d:
        for param in d['sub_params']:
            parse(**d['sub_params'][param])
        add_param(d)
    else:
        add_param(d)


def setup(manifest):
    with open(manifest, 'r') as f:
        mani = json.loads(f.read())
        for p in mani['board'].values():
            parse(**p)

params = {}
params.update(**parameters.params)
params.update(**esp32_driver.params)
iris = Iris(adr=36, fault_bits=8, header_bits=29, ad_bits=10, priority_bits=3)

setup('manifest.json')

print('setup complete')
def test():
    iris.p[10].write(True)
    iris.p[25].write(True)
    iris.p[28].write(True)
    utime.sleep_ms(500)
    iris.p[10].write(False)
    iris.p[25].write(False)
    iris.p[28].write(False)
    for i in range(50):
        iris.p[31].write(i*10)
        utime.sleep_ms(20)
    for i in range(50):
        iris.p[31].write((50-i)*10)
        utime.sleep_ms(25)
    # utime.sleep_ms(1)
    iris.p[31].write(0)

def test_timers():
    iris.p[180].write(200)
    iris.p[181].write(200)
    iris.p[182].write(200)
    iris.p[183].write(200)
    utime.sleep_ms(500)
    print(iris.t.t, iris.t._t)
    iris.t.chk()
    print(iris.t.t, iris.t._t)
    iris.t.chk()
    print(iris.t.t, iris.t._t)
    iris.t.chk()
    print(iris.t.t, iris.t._t)
    iris.t.chk()
    print(iris.t.t, iris.t._t)

iris.p[430].write(b'\x00\x0a\x00')
iris.p[431].write(b'\x00\x0a\x00\x00\x00\x0a')
test()
iris.p[100].write(None) #test operator
test_timers()



iris.report()
iris.p[430].write(b'\x00\x00\x00')
iris.p[431].write(b'\x00\x00\x00\x00\x00\x00')
while True:
    iris.chk()
    utime.sleep_ms(50)



