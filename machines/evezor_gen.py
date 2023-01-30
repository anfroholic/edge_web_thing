import json
# import pprint
# from datetime import datetime
# import gcode_conversion as gc
import math

"""
This is the current working version for evezor.py 
The next iteration is nested objects but needs a lot of work to bring it to the level this one is
"""


# pp = pprint.PrettyPrinter(indent=4)


class Machine:
    # TODO: make objects add something to machine so machine can post about itself
    def __init__(self, **_config):
        """
        Create Machine
        kwargs: config
        machines is a json file with machine definitions
        """
        with open(_config['config']) as f:
            config = json.load(f)
        self.config = config
        self.axes = config['axis_labels']
        self.name = config['name']
        print(f'machine name: {self.name}')
        print(self.axes)

        # setup motion helpers
        self.current_position = {}
        for axis in self.axes:
            self.current_position[axis] = None
        self.current_position['feed'] = None
        self.previous_position = self.current_position.copy()

        # Set up repos for tools and accessories
        self.accessories = {}
        self.current_tool = None
        self.work_offset = {'x': 0}
        self.tool_offset = {}

        # Set up repo for created code
        self.state = 'post'
        self.the_post = {'comments': None, "program": []}

        # self.the_post['comments'] = f"""# this file was created with {__file__}# on {datetime.now()}"""

    def list_accessories(self):
        print(list(self.accessories.keys()))

    def show_state(self):
        print('Current machine postition:')
        print(self.current_position)
        print(f'Work offset {self.work_offset}')


class Move:
    """
    Move cmd sent to machine class
    """

    def __init__(self, machine):
        self.machine = machine

    def linear(self, **cmd):
        """
        Executes a move in a straight line from the current position
        kwargs: [any available axis] and feed  eg. 'x', 'y', 'theta', 'feed'
        """
        # print(cmd)

        for axis in self.machine.axes:
            if axis in cmd:
                if axis in self.machine.work_offset:
                    cmd[axis] += self.machine.work_offset[axis]
                if axis in self.machine.tool_offset:
                    cmd[axis] += self.machine.tool_offset[axis]
                self.machine.current_position[axis] = cmd[axis]

        if 'feed' in cmd:
            self.machine.current_position['feed'] = cmd['feed']
        # print(cmd)
        # post the thing
        post = {'cmd': 'move.linear'}
        for key in self.machine.current_position:
            if self.machine.current_position[key] != self.machine.previous_position[key]:
                post[key] = round(self.machine.current_position[key], 3)
        if 'comment' in cmd:
            post['comment'] = cmd['comment']
        # to_post_or_not_to_post(post)

        # set the previous location to machine for next run
        for key in self.machine.current_position:
            self.machine.previous_position[key] = self.machine.current_position[key]

        yield post

    def rapid(self, **cmd):
        """
        Executes a rapid move
        **Warning** Move may be non-linear, be sure to have proper clearance
        kwargs: [any available axis] and feed  eg. 'x', 'y', 'theta', 'feed'
        """
        for axis in self.machine.axes:
            if axis in cmd:
                if axis in self.machine.work_offset:
                    cmd[axis] += self.machine.work_offset[axis]
                if axis in self.machine.tool_offset:
                    cmd[axis] += self.machine.tool_offset[axis]
                self.machine.current_position[axis] = cmd[axis]

        # post the thing
        post = {'cmd': 'move.rapid'}
        for key in self.machine.current_position:
            if not self.machine.current_position[key] == self.machine.previous_position[key]:
                post[key] = self.machine.current_position[key]
        if 'comment' in cmd:
            post['comment'] = cmd['comment']
        # to_post_or_not_to_post(post)

        for key in self.machine.current_position:
            self.machine.previous_position[key] = self.machine.current_position[key]

        yield post

    def home(self, **cmd):
        """
        Moves machine to endstops or executes applicable find home routine
        kwargs: [any available axis] and will only execute on said axes
        Homing feedrate and other settings found in config
        """
        cmd['cmd'] = 'move.home'
        yield cmd


def drill(**kwargs):
    #  TODO: add kwarg to choose axis for drilling
    # move to the hole
    hole = {}
    if 'x' in kwargs.keys():
        hole['x'] = kwargs['x']
    if 'y' in kwargs.keys():
        hole['y'] = kwargs['y']
    if (hole):
        hole['cmd'] = 'move.rapid'

        yield hole
        # machine.the_post['program'].append(hole)

    # do the drill
    peck_start = machine.current_position['z']
    # TODO refactor work offsets into 'machine' function
    bottom = machine.current_position['z']
    # if 'z' in machine.work_offset:
    #     bottom += machine.work_offset['z']
    # if 'z' in machine.tool_offset:
    #     bottom += machine.tool_offset['z']
    bottom += kwargs['bottom']
    peck_depth = kwargs['peck_depth']
    num_pecks = (peck_start - bottom) / peck_depth
    num_pecks = math.ceil(num_pecks)  # round up
    retract_height = kwargs['retract_height']
    if 'z' in machine.work_offset:
        retract_height += machine.work_offset['z']
    if 'z' in machine.tool_offset:
        retract_height += machine.tool_offset['z']

    for peck in range(num_pecks):
        # drill
        depth = round(peck_start - ((peck + 1) * peck_depth), 3)
        if depth < bottom:  # are we at the bottom?
            depth = bottom
        engage = {'cmd': 'move.linear',
                  'z': depth + peck_depth,
                  'feed': kwargs['retract_feed']
                  }
        yield engage

        _drill = {'cmd': 'move.linear',
                  'z': depth,
                  'feed': kwargs['feed']
                  }

        yield _drill

        # machine.the_post['program'].append(_drill)

        # retract
        _retract = {'cmd': 'move.linear',
                    'z': retract_height,
                    'feed': kwargs['retract_feed']
                    }

        yield _retract

        # machine.the_post['program'].append(_retract)


print('starting evezor')
# setup
# import os
# print(os.listdir())
machine = Machine(config='machine_config.json')
move = Move(machine)

if __name__ == '__main__':
    print('loaded')
