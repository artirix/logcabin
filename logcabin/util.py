import time
import gevent

class ConfigException(Exception):
    pass

def dynamic_class(modname, classname):
    mod = __import__(modname)
    # import returns the top-level module, so recurse to the sub module
    for m in modname.split('.')[1:]:
        mod = getattr(mod, m)
    return getattr(mod, classname)

class BroadcastQueue(list):
    """Queue-like object that broadcasts to all child queues."""

    def put(self, obj):
        for q in self:
            q.put(obj)

    def join(self):
        for q in self:
            q.join()

class Periodic(gevent.Greenlet):
    """Greenlet wrapper that periodically makes a callback."""
    
    def __init__(self, period, callback):
        super(Periodic, self).__init__()
        self.period = period
        self.callback = callback

    def _run(self):
        now = time.time()
        next = now + self.period
        while True:
            while next < now:
                next += self.period
            gevent.sleep(next - now)
            self.callback()
            now = time.time()

def get_path(d, path):
    """Get a nested dictionary values, supporting wildcard '*' matches at any level

    >>> sorted(get_path({'a': 1, 'b': 2}, 'a'))
    [('a', 1)]
    >>> sorted(get_path({'a': 1, 'b': 2}, '*'))
    [('a', 1), ('b', 2)]
    >>> sorted(get_path({'a':{'b':{'c': 1}}}, 'a.b.c'))
    [('a.b.c', 1)]
    >>> sorted(get_path({'a': {'b': {'c': 1}, 'd': {'c': 2}}, 'b': {'b': {'c': 3}}}, 'a.*.c'))
    [('a.b.c', 1), ('a.d.c', 2)]
    >>> sorted(get_path({}, 'a.*.c'))
    []
    >>> sorted(get_path({'a': 1}, 'a.b'))
    []
    >>> sorted(get_path({'a': 1}, 'a.*'))
    []
    """

    matches = [([], d)]
    parts = path.split('.')
    for part in parts:
        previous = matches
        matches = []
        
        for key, d in previous:
            if isinstance(d, dict):
                if part == '*':
                    matches.extend((key+[k], v) for k, v in d.iteritems())
                elif isinstance(d, dict) and part in d:
                    matches.append((key+[part], d[part]))

    return [ ('.'.join(k), v) for k, v in matches ]
