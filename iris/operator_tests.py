
def string_to_int_list(s):
    list(s.encode())


def pin(_pin):
    print('setup pin: {} in hardware'.format(_pin))


def can_send(**m):
    print('sending can mess: {}'.format(m))


def reset(state):
    print('resetting board')


def test(state):
    return 'test passed, arg:{}'.format(state)
