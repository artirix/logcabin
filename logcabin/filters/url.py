import urlparse

from .filter import Filter

class Url(Filter):
    """Parse a field with a regular expression. The regex named groups
    ``(?P<name>...)`` will be create event fields (overwriting any existing).

    If you extract a 'timestamp' field, this will automatically be parsed as a
    datetime and used as the event timestamp (instead of the default of the time
    received).

    :param string field: the field to run the regex on (default: data)
    """

    def __init__(self, field='data', on_error='reject'):
        super(Url, self).__init__(on_error=on_error)
        self.field = field

    def process(self, event):
        if self.field in event:
            url = event.pop(self.field)
            url.split('?', 1)
            r = urlparse.urlparse(url)
            event['path'] = r.path
            # for simplicity, ignore repeated parameters
            event.update(dict(urlparse.parse_qsl(r.query)))
