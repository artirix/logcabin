import re
import dateutil.parser

from .filter import Filter

class Regex(Filter):
    """Parse a field with a regular expression. The regex named groups
    ``(?P<name>...)`` will be create event fields (overwriting any existing).

    If you extract a 'timestamp' field, this will automatically be parsed as a
    datetime and used as the event timestamp (instead of the default of the time
    received).

    :param string regex: the regular expression
    :param string field: the field to run the regex on (default: data)

    Example::

        Regex(regex='(?P<timestamp>.+) - (?P<message>.+)')
    """

    def __init__(self, regex, field='data', on_error='reject'):
        super(Regex, self).__init__(on_error=on_error)
        self.field = field
        self.regex = re.compile(regex)

    def process(self, event):
        if self.field in event:
            data = event.pop(self.field)
            m = self.regex.search(data)
            if m:
                d = m.groupdict()
                if 'timestamp' in d:
                    # if the originating timestamp is being extracted, convert
                    # it to a datetime
                    d['timestamp'] = dateutil.parser.parse(d['timestamp'])
                self.logger.debug('Matched: %s' % d)
                event.update(d)
            else:
                self._error(event, 'no match')
