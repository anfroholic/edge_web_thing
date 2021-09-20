the_conversions = {
    'move.linear': 'G1',
    'move.rapid': 'G0',
    'suck.on': None,
    'suck.off': None,
    'feed.feeder': None,
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
                    blurb = '{}{} '.format(axes[axis],val)
                    line += blurb
            if 'feed' in kwargs:
                blurb = "F{}".format(kwargs['feed'])
                line += blurb

        elif command == 'feed.feeder':
            line = "feeding the feeder {}".format(kwargs['id'])

        elif command == 'suck.on':
            line = 'turn on suction'

        elif command == 'suck.off':
            line = 'turn off suction'

    else:
        print('WARNING: UNKNOWN COMMAND in gcode_conversion')
        print(kwargs)
    # print(line)
    return line
