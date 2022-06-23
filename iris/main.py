print('loading')
import json
import parameters
import esp32_driver
import gc
gc.collect()

from iris import Iris

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

class Test:
    def __init__(self, name):
        self.name = name
        print('{} initialized'.format(self.name))
    
    def __call__(self):
        print('{} testing'.format(self.name))

test = Test('tester')
