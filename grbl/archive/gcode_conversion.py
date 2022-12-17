from machine import UART, CAN
print('gcode_conversion v1.0 loaded')
the_conversions = {
    'move.linear': 'G1',
    'move.rapid': 'G0',
    'sleep': 'G4',
    'suction': 399,
    'feed.feeder': 398,
    'ring_light': 397,
    'spindle.on': 1181,
    'spindle.off': 1180,
    'vise': 1196,
    'coolant': 1195,
    'spindle': 1492
}

axes = {
    'x': 'X',
    'y': 'Y',
    'z': 'Z',
    'a': 'A',
    'b': 'B',
    'c': 'C'
}


def convert(**kwargs):
    # print(kwargs)
    """
    Convert json line into gcode
    :param kwargs:
    :return:
    """
    line = None
    # print('converting')
    # print(kwargs)
    if kwargs['command'] in the_conversions.keys():
        command = kwargs['command']
        # print(command)
        if command == 'move.linear' or command == 'move.rapid':
            line = the_conversions[kwargs['command']] + ' '
            for axis in axes.keys():
                if axis in kwargs.keys():
                    val = kwargs[axis]

                    val = round(float(val), 3)
                    blurb = '{}{} '.format(axes[axis], val)
                    line += blurb
            if 'feed' in kwargs:
                blurb = "F{}".format(kwargs['feed'])
                line += blurb

        elif command == 'sleep':
            line = '{} P{}'.format(the_conversions[command], kwargs['val'])

        else:
            line = 'can message: {} arb: {} val: {}'.format(command, the_conversions[command], kwargs['val'])
            print('{}, {}'.format(the_conversions[command], mess))

    else:
        print('WARNING: UNKNOWN COMMAND in gcode_conversion')
        print(kwargs)
    # print(line)
    return line
