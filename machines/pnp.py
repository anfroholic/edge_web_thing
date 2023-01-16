from machines.evezor_gen import *
# import csv
import json
# import pprint

# pp = pprint.PrettyPrinter(indent=4)
"""
Parses footprint file and generates pick routines
"""

pos_file = 'GRBL_5x-top-pos'

config = {
         'z_clear': 16,
         'rack_file': 'the_rack.json',
         'feed': 15000,
         'nozzle_offset': {'x': -16.4, 'y': 70.2},
         'debug': True
}

class PNP:
    def __init__(self, z_clear, rack_file, feed, nozzle_offset, debug=True):
        self.z_clear = z_clear
        self.board_offset = {'x': 0, 'y': 0, 'z': 0}
        self.nozzle_tool_offset = nozzle_offset
        self.rack = self.load_rack(rack_file)
        self.feed = feed
        self.debug = debug
        self.components = None
        self.skipped_components = set()

    def create_gen(self, board_offset, pos_file):
        self.skipped_components.clear()

        machine.tool_offset = self.nozzle_tool_offset
        self.board_offset = board_offset
        components = self.open_file(pos_file)
        print('is gen', components)

        print(next(components))  # handle csv headers
        yield from self.parse_components(components)
        # send machine home
        machine.tool_offset = {}
        yield from move.linear(x=50, y=350, feed=5000, comment='go home')

        if self.debug:
            print('Skipped Components')
            for component in self.skipped_components:
                print(component)

    def parse_components(self, components):
        prev_component = None
        for component in components:
            component = self.component_to_list(component)
            if component[1] not in self.rack:
                # print('skipping', component)
                self.skipped_components.add(component[1])
                # yield
            else:
                if prev_component is None:
                    # handle first component
                    print('first comp')
                    yield from self.feed_feeder(component)
                    yield {'cmd': 'sleep', 'val': 4}
                    prev_component = component
                else:
                    yield from self.pick(prev_component)
                    yield from self.feed_feeder(component)
                    yield from self.place(prev_component)
                    prev_component = component
        else:
            yield from self.pick(prev_component)
            yield from self.place(prev_component)


    @staticmethod
    def open_file(csv_file):
        with open(f'{csv_file}.csv', 'r')as f:
            for line in f:
                yield line.strip()

    @staticmethod
    def load_rack(rack_file) -> dict:
        with open(rack_file) as j:
            rack = json.load(j)
        return rack

    def feed_feeder(self, component):
        yield {
            'cmd': 'feed.feeder',
            'val': self.rack[component[1]]['id'],
            'comment': f"{component[1]}, {component[0]}"}

    @staticmethod
    def component_to_list(component: str) -> list:
        """convert """
        component = component.split(',')
        component[0] = component[0].strip('"')
        component[1] = component[1].strip('"')
        component[2] = component[2].strip('"')
        component[3] = float(component[3])
        component[4] = float(component[4])
        component[5] = float(component[5])
        return component



    def pick(self, component):
        # print(f"picking {component}")
        machine.work_offset = {}
        comp = self.rack[component[1]]

        yield from move.linear(x=comp['x'], y=comp['y'], a=comp['a'], feed=self.feed)
        yield from move.linear(z=comp['z'])
        yield {'cmd': 'suction', 'val': 1}
        yield {'cmd': 'sleep', 'val': 1}
        yield from move.linear(z=self.z_clear)


    def place(self, component):
        # print(f"placing {component}")
        machine.work_offset = self.board_offset

        yield from move.linear(x=component[3], y=component[4], a=component[5], feed=self.feed)
        yield from move.linear(z=0)
        yield {'cmd': 'suction', 'val': 0}
        yield {'cmd': 'sleep', 'val': 1}
        machine.work_offset = {}
        yield from move.linear(z=self.z_clear, comment='part placed moving z')

def export_to_file(generator, file):
    with open(f'{file}.txt', "w") as f:
        for line in generator:
            f.write(f'{json.dumps(line)}\n')


if __name__ == '__main__':
    board_work_offset = {'x': 295.5, 'y': 307.2, 'z': 0}
    # board_work_offset = {'x': 185.5, 'y': 292.6, 'z': 0}  # this is for the joy pad

    print('Parsing footprints')
    pnp = PNP(**config)

    this = pnp.create_gen(board_work_offset, pos_file=pos_file)

    export_to_file(this, pos_file)

