from parameters import Parameter
import machine
from machine import Pin
import utime
# import machine
#
#
# class Freq(parameters.Parameter):
#     def __init__(self, name, **k):
#         super().__init__(name, **k)
#
#     def write(self, state):
#         super().write(state)
#         self.hw()
#
#     def hw(self):
#         machine.freq(self.state)
#
#
# class Msgr(parameters.Parameter):
#     def __init__(self, name, **k):
#         super().__init__(name, **k)
#         self.buf = bytearray(8)
#         self.mess = [0, 0, 0, memoryview(self.buf)]
#         self.can = CAN(0,
#                        tx=k['tx'],
#                        rx=k['rx'],
#                        extframe=k['extframe'],
#                        mode=k['mode'],
#                        baudrate=k['baudrate'])


class PWM(Parameter):
    def __init__(self, **k):
        super().__init__(**k)
        self.invert = self.p[k['sub_params']['invert']['id']]
        self.freq = self.p[k['sub_params']['freq']['id']]
        self.duty = self.p[k['sub_params']['duty']['id']]
        # hold its own state, so it may be referenced in poke()
        self._freq = self.freq.state
        self._duty = self.duty.state

        # Set up hardware
        self.pin = machine.PWM(k['pin'], freq=self._freq)
        self.pin.duty(0)
        self.iris.hw_outs.append(self.pid)

    def write(self, state):
        super().write(state)
        if self.state != state:
            self.hw(state)

    def hw(self, state):
        if state:
            print('init pwm with {} and {}'.format(self._freq, self._duty))
        else:
            print('de init pwm')

    def poke(self):
        print('I think this method is needed for fast updates')
        if self._duty != self.duty.state:
            print('update the duty')
            self._duty = self.duty.state
        if self._freq != self.freq.state:
            print('update the freq')
            self._freq = self.freq.state


class DigitalOutput(Parameter):
    def __init__(self, **k):
        super().__init__(**k)
        self.invert = self.p[k['sub_params']['invert']['id']]
        self.pin = Pin(k['pin'], mode=Pin.OUT)
        self.iris.hw_outs.append(self.pid)

    def write(self, state) -> None:
        super().write(state)
        self.hw()

    def hw(self):
        if self.invert.state:
            print("writing pin: to {}".format(not self.state))
            self.pin.value(not self.state)
        else:
            print("writing pin: to {}".format(self.state))
            self.pin.value(self.state)


class AnalogInput(Parameter):
    def __init__(self, **k):
        super().__init__(**k)
        self.sample_rate = self.p[k['sub_params']['sample_rate']['id']]
        self.low = self.p[k['sub_params']['low']['id']]
        self.high = self.p[k['sub_params']['high']['id']]
        # Set up hardware
        # self.pin = driver.ADC(k['pin'])
        self.iris.h.append(k['id'])

        print('setting up analogInput({}, low={}, high={})'.format(k["pin"], self.low.state, self.high.state))

    def chk(self):
        print('code for checking the input adc with {}'.format(self.sample_rate))
        print('if the state has changed it pushes to self.write()')


class DigitalInput(Parameter):
    def __init__(self, **k):
        super().__init__(**k)
        self.debounce = self.p[k['sub_params']['debounce']['id']]
        self.invert = self.p[k['sub_params']['invert']['id']]
        # Set up hardware
        # self.pin = Pin(k['pin'], mode=k['pin_mode'], pull=k['pin_pull'])
        if 'pull' in k:
            if k['pull'] == 'up':
                self.pin = Pin(k['pin'], mode=Pin.IN, pull=Pin.PULLUP)
            else:
                self.pin = Pin(k['pin'], mode=Pin.IN, pull=Pin.PULLDOWN)
        else:
            self.pin = Pin(k['pin'], mode=Pin.IN)
        self.iris.h.append(k['id'])

    def chk(self):
        # print(f'code for checking the input {self.pin}')
        print('if the state has changed it pushes to self.write()')


class Reset:
    def __init__(self, **k):
        self.id = k['id']
        self.state = k['state']

    @staticmethod
    def write(self, *state):
        machine.reset()

params = {
    'AnalogInput': AnalogInput,
    'PWM': PWM,
    'DigitalOutput': DigitalOutput,
    'DigitalInput': DigitalInput
}
