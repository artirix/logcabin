from .filter import Filter

class Mutate(Filter):
    """Filter that allows you to add, rename and drop fields

    :param map set: fields to set (optional)
    """
    def __init__(self, set={}):
        super(Mutate, self).__init__()
        self.sets = set
        assert type(self.sets) == dict
    
    def process(self, event):
        for k, v in self.sets.iteritems():
            event[k] = v
            self.logger.debug('Set %s to %s' % (k, v))
