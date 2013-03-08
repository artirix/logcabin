from .filter import Filter
import re

class Regex(Filter):
    """Parse a field with a regular expression. The regex named groups
    (?P<name>...) will be create event fields (overwriting any existing).

    :param string field: the field to run the regex on (default: data)
    :param string regex: the regular expression
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
                event.update(m.groupdict())
            else:
                self._error(event, 'no match')
