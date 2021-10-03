the_conversions = {
    'move.linear': 'G1',
    'move.rapid': 'G0',
    'sleep': 'G4',
    'suction': 399,
    'feed.feeder': 398,
    'ring_light': 397,
    'spindle.on': None,
    'spindle.off': None
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
            line = '{} {}'.format(the_conversions[command], kwargs['val'])

        else:
            line = 'can message: {} arb: {} val: {}'.format(command, the_conversions[command], kwargs['val'])
            # can.send(kwargs['val'], the_conversions[command])
    else:
        print('WARNING: UNKNOWN COMMAND in gcode_conversion')
        print(kwargs)
    # print(line)
    return line
