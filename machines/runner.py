

class Loader:
    """
    returns generator objects for CNC
    """

    def __init__(self, **k):
        pass

    def __call__(self, item, *args, **kwargs):
        if type(item) is str:
            return self._open(item)
        elif type(item) is list:
            return self._load(item)
        elif item.__class__.__name__ == 'function':
            return item(*args, **kwargs)
        elif item.__class__.__name__ == 'generator':
            try:
                return item()  # upython handles this poorly
            except TypeError:
                return item

    @staticmethod
    def _load(_list):
        yield from _list

    @staticmethod
    def _open(file):
        with open(file, 'r') as f:
            for line in f:
                yield json.loads(line.strip())


class Runner:
    def __init__(self, name, subs={}):
        self.name = name
        self.callback = None
        self.loader = Loader()
        self.gens = []
        self.g = None
        self.subs = subs
        self.sub_pid = None

    def load_script(self, script, *args, **kwargs):
        if self.g:  # if we're already in the middle of a script, store it for later
            self.gens.append(self.g)
        self.g = self.loader(script)

    def __call__(self, state):
        print('checking for callback now', self.callback)
        if self.callback(state):
            if self.sub_pid:
                self.subs.pop(self.sub_pid)
                self.sub_pid = None
            next(self)

    def __next__(self):
        while True:
            try:
                line = next(self.g)
                
                if line['cmd'] == 'callback':
                    print('got callback')
                    self.callback = line['callback']
                    if 'pid' in line:  # there may be functions from self that will not arrive in mailbox
                        self.sub_pid = line['pid']
                        self.subs[self.sub_pid] = 69
                    break
                
                elif line['cmd'] == 'load':  # load a text file
                    print(f'loading {line["script"]}')
                    self.load_script(line['script'])
                
                elif line['cmd'].__class__.__name__ == 'function' or \
                                 line['cmd'].__class__.__name__ == 'method' or \
                                 line['cmd'].__class__.__name__ == 'bound_method':
                    
                    copy = line.copy()
                    should_break = False
                    if 'callback' in line:  # when starting a cnc routine, we're not breaking for a long running event
                        self.callback = copy.pop('callback')
                        should_break = True
                    
                    func = copy.pop('cmd')
                    func(**copy)
                    
                    if should_break:
                        break
                else:
                    print(line)

            except StopIteration:
                if self.gens:
                    self.g = self.gens.pop()
                else:
                    print('job complete')
                    break
