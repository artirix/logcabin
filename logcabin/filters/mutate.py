import types

from .filter import Filter

class Mutate(Filter):
    """Filter that allows you to add, rename, copy and drop fields

    :param map set: fields to set (optional). The values if strings may format other fields from the event.
    :param map rename: fields to rename (a: b renames b to a) (optional)
    :param list unset: fields to unset (optional)

    Example::

        Mutate(set={'fullname': '{first} {last}'})

    Renaming::

        Mutate(rename={'@timestamp': 'timestamp', '@message': 'message'})

    Unsetting::

        Mutate(unset=['junk', 'rubbish'])
    """
    def __init__(self, set={}, rename={}, copy={}, unset=[]):
        super(Mutate, self).__init__()
        self.sets = set
        assert type(self.sets) == dict
        self.renames = rename
        assert type(self.renames) == dict
        self.copies = copy
        assert type(self.copies) == dict
        self.unsets = unset
        assert type(self.unsets) == list
    
    def process(self, event):
        for k, v in self.sets.iteritems():
            if isinstance(v, types.StringTypes):
                v = event.format(v)
            event[k] = v
            self.logger.debug('Set %r to %r' % (k, v))

        for k, v in self.renames.iteritems():
            if v in event:
                event[k] = event.pop(v)
                self.logger.debug('Renamed %r to %r' % (v, k))

        for k, v in self.copies.iteritems():
            if v in event:
                event[k] = event[v]
                self.logger.debug('Copied %r to %r' % (v, k))

        for k in self.unsets:
            if k in event:
                del event[k]
                self.logger.debug('Unset %r' % (k,))
