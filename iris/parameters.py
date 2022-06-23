from iris import Iris
import struct
import operator_tests

class Blob:
    def __init__(self, *, blob: list, parent_id: int):
        # blob [active, bus.broadcast, self.broadcast, debug, hot]
        self.parent_id = parent_id
        self.pid = blob[1]
        self.state = blob[0]

    def write(self, state) -> None:
        # TODO: make this also update its own manifest so this persists after reboot
        self.state = state


class Parameter:  # Abstract class
    def __init__(self, *, id: int, state: any, d_type: list[str, str], blob: int, hot=None, iris: Iris,
                 **k):
        self.pid = id
        self.state = state
        self.struct = d_type[1]
        self.p = iris.p
        self.iris = iris

        # self.p[blob[1]] = Blob(blob=blob, parent_id=self.pid)
        # self.blob = self.p[blob[1]]
        self.blob = blob

        if d_type[0] == 'range':  # is this param a range type
            self.low = self.p[k['sub_params']['low']['id']]
            self.high = self.p[k['sub_params']['high']['id']]
        if hot is not None:  # does this param have a hot route
            self.hot = hot

    def write(self, state) -> None:
        if state is not None:
            self.state = state
        print('current state is {}'.format(self.state))
        self.send()

    def send(self) -> None:
        if self.blob & 1:
            if self.blob & 2:
                print('sending')
                self.iris.send(pid=self.pid, load=struct.pack(self.struct, self.state), w=False)
            if self.blob & 4:
                self.iris.send_i({self.pid: self.state})
            if self.blob & 8:
                print('make debug routine')
            if self.blob & 16:
                self.p[self.hot].write(self.state)


class Switch(Parameter):
    """Note: Switches may only speak to parameters on self"""

    def __init__(self, *, switch: list[int], **k):
        super().__init__(**k)
        self.switch = switch  # list of agents in switch

    def write(self, state):
        if state is not None:
            self.state = state
            self.do_it()
        else:
            self.do_it()

    def do_it(self):
        print('switch triggered, state:{}, to pid:{}'.format(self.state, self.switch[self.state]))
        if self.blob.state[0] == 'T':
            self.p[self.switch[self.state]].write(None)


class Branch(Parameter):
    """Note: Truths may only speak to parameters on *this* board"""

    # TODO: test this
    def __init__(self, **k):
        super().__init__(**k)
        self.true = k['true']
        self.false = k['false']

    def write(self, state):
        if state is not None:
            self.state = state
            self.test()
        else:
            self.test()

    def test(self):
        if self.blob & 1:
            if self.state:
                self.p[self.true].write(None)
            else:
                self.p[self.false].write(None)


class Timer(Parameter):
    """Currently Untested"""

    def __init__(self, **k):
        super().__init__(**k)

    def write(self, duration):
        if duration is not None:
            try:
                index = [t[1] for t in self.iris.t].index(self.pid)
                self.iris.t[index][0] = duration
            except ValueError:
                self.iris.add_tim([duration, self.pid])
                self.state = True
        else:
            super().write(None)

    def ding(self):
        """Timer goes ding"""
        self.state = False
        self.iris.rem_tim(self.pid)
        super().write(True)

    def poke(self):
        """stop the timer"""
        self.state = False
        self.iris.rem_tim(self.pid)
        print("removing timer from iris' list")


class Operator(Parameter):
    def __init__(self, **k):
        super().__init__(**k)
        self.code = k['code']

    def read(self):
        return self.state

    def write(self, state):
        if type(state) == str:
            expr = self.code.replace('state', '\"{}\"'.format(state))
        else:
            expr = self.code.replace('state', str(state))
        print(expr)
        self.state = eval(expr)
        print(self.state)


# class IOperator(Parameter):
#     def __init__(self, **k):
#         super().__init__(**k)
#         self.code = k['code']
# 
#     def read(self):
#         return self.state
# 
#     def write(self, state):
#         self.state = eval(self.code, {**__builtins__}, {'iris': self.iris, 'self': self})
#         print(self.state)


class State(Parameter):

    def __init__(self, **k):
        super().__init__(**k)

    def read(self):
        return self.state

    def write(self, state):
        super().write(state)
        # self.iris.change_state(self.state)


class Basic(Parameter):
    """Basic class for Arithmetic, Logical, and Comparison"""

    # TODO: test this
    def __init__(self, *, input_a, input_b, operator, **k):
        super().__init__(**k)
        self.a = input_a
        self.b = input_b
        self.op = operator

    def write(self, state):
        if state is not None:
            print('{}, {}'.format(self.p[self.a].state, self.p[self.b].state))

            print(eval('self.p[{}].state {} self.p[{}].state'.format(self.a, self.op, self.b)))
            super().write(eval('self.p[{}].state {} self.p[{}].state'.format(self.a, self.op, self.b)))
        else:
            super().write(None)


class Variable(Parameter):
    def __init__(self, *, poke=None, **k):
        super().__init__(**k)
        if poke is not None:
            self.poke = poke

    def write(self, state):
        super().write(state)

        if hasattr(self, 'poke'):
            self.p[self.poke].poke()


class Clamp(Parameter):
    def __init__(self, **k):
        super().__init__(**k)
        # high and low are created in the Superclass
        self._low = self.p[k['parent']].low
        self._high = self.p[k['parent']].high
        self.dir = k['dir']  # direction: are we clamping from self to bus or reverse

    def write(self, state):
        if state is not None:
            super().write(round(self.do_the_clamp(state)))
        else:
            super().write(self.state)

    def do_the_clamp(self, state):
        if self.dir == 'F':
            if state < self._low.state:
                state = self._low.state
            return ((state - self._low.state) / (self._high.state - self._low.state)) * \
                   (self.high.state - self.low.state) + self.low.state


class Decimal(Variable):
    """Not Tested or Implemented"""

    def __init__(self, **k):
        super().__init__(**k)
        self.power = self.p[k['sub_params']['power']['id']]


class StrBuf(Parameter):
    def __init__(self, **k):
        super().__init__(**k)
        self.buf = None  # buffer
        self.encode = 'utf-8'

    def write(self, state):
        if b'\x04' in state:  # end of string transmission
            self.buf += state
            self.process_buf()
        self.buf += state

    def process_buf(self):
        end = self.buf.find(b'\04')
        self.buf = self.buf[:end].decode(self.encode)
        self.write(self.buf)


params = {
    'Variable': Variable,
    'Operator': Operator,
    'Clamp': Clamp,
    'Branch': Branch,
    'Basic': Basic,
    'Timer': Timer,
    'Switch': Switch,
    'State': State
}

if __name__ == '__main__':
    print('loaded')
