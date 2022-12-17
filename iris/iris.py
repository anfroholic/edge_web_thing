import struct


class Header:
    def __init__(self, *, adr: int, header_bits: int, ad_bits: int, priority_bits, **k):
        """
        package [parameter priority bits][address bits][parameter bits]
        """
        self.adr = adr # this board's address
        self.header_bits = header_bits
        self.ad_bits = ad_bits  # bits in address field
        self.priority_bits = priority_bits
        self.ad_mask = 2**self.ad_bits - 1

        # constants for unpacking
        self.num_low = self.header_bits - self.ad_bits - self.priority_bits
        self.low_mask = 2**self.num_low-1 # also includes write bit
        self.high_mask = (2**self.priority_bits - 1) << (self.num_low + self.ad_bits) # also includes write bit

        # constants for packing
        self.low_shft = self.num_low - 1
        self.pk_mask = 2 ** (self.low_shft) - 1


    def unpack(self, h: int) -> tuple[int, int, int]:
        # print(h)
        low = h & self.low_mask
        high = h & self.high_mask
        hdr = (
            h & 1,  # w
            h >> self.num_low & self.ad_mask,  # ad
            ((high >> self.ad_bits) + low) >> 1,  # pid
        )
        return hdr

    def pack(self, pid: int, w: bool, ad: int):
        high = pid >> self.low_shft
        low = pid & self.pk_mask
        hdr = ((((high << self.ad_bits) + ad) << self.low_shft) + low) << 1

        if w:
            hdr += 1
        return hdr


class Message(Header):
    def __init__(self, *, adr: int, s: dict[int:int], p, fault_bits, **k):
        super().__init__(adr=adr, **k)
        self.fault = 2**fault_bits
        self.adr = adr
        self.s = s
        self.p = p
        # single items, len(bytearray) is 8 or less
        self.single = {'b': 1,
                       'B': 1,
                       '?': 1,
                       'h': 2,
                       'H': 2,
                       'i': 4,
                       'I': 4,
                       'q': 8,
                       'Q': 8,
                       'f': 4,
                       'd': 8
                       }

    def want(self, h: int) -> bool:
        print(h)
        # This must be Fast
        if h < self.fault:  # emergency
            return True
        elif self.adr == (h >> self.num_low) & self.ad_mask:  # message for self
            return True
        elif h in self.s:  # in subscriptions?
            return True
        else:
            return False

    def process(self, load: bytearray, header: int):

        print(load)
        print('testing')

        w, ad, pid = self.unpack(header)
        print(self.unpack(header))

        if ad == 0:
            if pid < self.fault:
                print('we are dangerous here. Emergency')
            else:
                print('network message')
        if ad == self.adr:
            # This message is for me or it's an imposter
            if w:
                self.write(load=load, bundle=self.p[pid].struct, pid=pid)
            else:
                print('we have an imposter, throw a fault')
        else:
            # subscription format: sub:{pid:pid, bundle:'struct'}
            self.write(pid=self.s[header]['pid'], bundle=self.s[header]['bundle'], load=load)


    def write(self, load: bytearray, pid: int, bundle: str) -> None:

        this = self.p[pid]

        if bundle in self.single:
            """unbundle single entity, eg. int, float, bool, etc."""
            # print(load, bundle, pid)
            this.write(struct.unpack(bundle, load[:self.single[bundle]])[0])

        elif bundle == 'buf':
            """do not unbundle, send byte array"""
            this.write(load)

        elif bundle == 'nibble':
            """
            nibble is a string with len(8) or less
            """
            length = 0
            for i in range(len(load)):
                print(load[i])
                if load[i] != 0:
                    length += 1
                else:
                    break
            s = "{}s".format(str(length))
            this.write(struct.unpack(s, load)[0].decode(this.encode))

        else:
            print('struct:{} must be a string or collection. *** Not handled yet ***'.format(bundle))


class Iris:
    def __init__(self, adr: int, **k):
        print('Iris initializing')
        self.adr = adr
        self.p = {}  # Parameter Table
        self.s = {}  # Subscription List

        self.msg = Message(adr=adr, s=self.s, p=self.p, **k)

        self.ib = []  # Inbox mess ready to be processed
        self.iib = []  # Internal mailbox
        self.ob = []  # Outbox
        self.t = []  # Active Timers
        self.h = []  # Hardware to .chk()
        self.hw_outs = []  # Hardware outputs
        # with open(manifest, 'r') as f:
        #     self.manifest = json.loads(f.read())

        # Boot
        # self.valid_mani = False
        # self.map_hash = None
        # self.valid_map = False

        # Stabilize
        # self.fault_checks = []  # Parameters subbed to outside places

    def chk(self):
        for hw in self.h:
            print(self.p[hw])
            self.p[hw].chk()

    # def report_all(self):
    #     for param in self.p:
    #         pprint.pprint(vars(iris.p[param]))

    def get(self, pid):
        return self.p[pid].state

    def send(self, **m):
#         if 'ad' in m:
#             h = self.msg.pack(pid=m['pid'], ad=m['ad'], w=m['w'])
#         else:
#             h = self.msg.pack(pid=m['pid'], ad=self.msg.adr, w=m['w'])
#         self.ob.append({'sub': h, 'load': m['load']})
        print('sending message: {} to outbox'.format(m))

    def send_i(self, m):
        self.iib.append(m)

    @staticmethod
    def can_send(m):
        # TODO: mess.pack here
        # driver.can_send(**m)
        # print(f'send message {m}')
        pass

    def add_tim(self, tim) -> None:
        self.t.append(tim)
        self.t.sort()
        # print(f'timer added:{self.t}')

    def rem_tim(self, tim_id) -> None:
        # print(f'remove timer with id:{tim_id}')
        print(self.t)
        print('timer removed')

    def chk_t(self):
        """Check the timers"""
        if self.t:
            print('{self.t[-1]} is the longest timer')
        else:
            print('no active timers')

    # def change_state(self, state):
    #     self.state = state
    #     if state == 0:  # Booting
    #         print('configure for boot')
    #     elif state == 1:  # Silent
    #         print('configure for Silent')
    #     elif state == 2:  # No hardware outputs: used to stabilize
    #         print('configure for No Hardware ')
    #     elif state == 3:  # Run
    #         print('configure for Run')
    #     elif state == 4:  # Fault Recovery
    #         print('configure for Fault Recovery')
    #     else:
    #         print('we are dangerous here, configure for Emergency')



if __name__ == '__main__':
    print('iris')
    iris = Iris(adr=36, fault_bits=8, header_bits=29, ad_bits=10, priority_bits=3)
    print(test := iris.msg.unpack(472186874))
    print(iris.msg.pack(**test))

