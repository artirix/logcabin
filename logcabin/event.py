import json
from string import Formatter
from datetime import datetime
from pprint import pformat
import dateutil.tz

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        import datetime
        if isinstance(obj, datetime.datetime):
            if obj.tzinfo is not None:
                # normalize all datetimes to UTC
                obj = obj.astimezone(dateutil.tz.tzutc()).replace(tzinfo=None)

            # isoformat doesn't produce consistent output when microsecond=0
            ms = '.%03dZ' % (obj.microsecond/1000)
            return obj.strftime("%Y-%m-%dT%H:%M:%S") + ms
        else:
            return super(JSONEncoder, self).default(obj)

class DefaultFormatter(Formatter):
    default = ''

    def get_value(self, key, args, kwargs):
        # Try standard formatting, then return 'unknown key'
        try:
            return Formatter.get_value(self, key, args, kwargs)
        except KeyError:
            return self.default

class Event(dict):
    """An event.

    This is the basic unit of communication in logcabin.
    """
    def __init__(self, *args, **kwargs):
        """
        Create an event. A timestamp is automatically generated.
        """
        if 'timestamp' not in kwargs:
            self['timestamp'] = datetime.utcnow()
        super(Event, self).__init__(*args, **kwargs)

    def add_tag(self, value):
        """
        Add a tag to the event.

        >>> ev = Event()
        >>> ev.add_tag('tag1')
        >>> ev.tags
        ['tag1']
        """
        self.setdefault('tags', []).append(value)

    @property
    def tags(self):
        """Get the tags for the event.

        >>> Event().tags
        []
        """
        return self.get('tags', [])

    def __getattr__(self, k):
        """Attribute getter for the dictionary elements, with None as default. Default makes
        safe to missing attributes in conditionals, etc.

        >>> Event().a
        >>> Event(a=2).a
        2
        """
        return self.get(k)

    def __setattr__(self, k, v):
        """Attribute setter for the dictionary elements.

        >>> ev = Event(timestamp=datetime(2013, 1, 1, 1, 2, 3, 45))
        >>> ev.a = 2
        >>> ev.b = ['1']
        >>> str(ev)
        "Event({'a': 2, 'b': ['1'], 'timestamp': datetime.datetime(2013, 1, 1, 1, 2, 3, 45)})"
        """
        self[k] = v

    def to_json(self):
        """Serialize the event to a json string.

        >>> from mock import patch
        >>> with patch('logcabin.event.datetime') as m:
        ...     m.utcnow.side_effect = lambda: datetime(2013, 1, 1, 2, 34, 56, 789012)
        ...     Event(field='x').to_json()
        '{"timestamp":"2013-01-01T02:34:56.789Z","field":"x"}'
        >>> Event(timestamp=datetime(2013, 1, 1, 1, 2, 3, 45)).to_json()
        '{"timestamp":"2013-01-01T01:02:03.000Z"}'
        """
        return json.dumps(self, cls=JSONEncoder, separators=(',', ':'))

    def format(self, fmt, args=None, raise_missing=False):
        """Format the event using string.format notation.

        >>> Event(field='x').format("field={field} missing={missing}")
        'field=x missing='
        >>> Event(field='x').format("field={field} arg1={0} arg2={1}", ['apple', 'pear'])
        'field=x arg1=apple arg2=pear'
        >>> from mock import patch
        >>> with patch('logcabin.event.datetime') as m:
        ...     m.utcnow.side_effect = lambda: datetime(2013, 1, 1, 2, 34, 56, 678912)
        ...     Event(field='x').format("{timestamp:%A %d. %B %Y}")
        'Tuesday 01. January 2013'
        """
        formatter = raise_missing and Formatter() or DefaultFormatter()
        return formatter.vformat(fmt, args, self)

    def __repr__(self):
        """Returns the representation of the object.

        >>> from mock import patch
        >>> with patch('logcabin.event.datetime') as m:
        ...     m.utcnow.side_effect = lambda: datetime(2013, 1, 1, 2, 34, 56)
        ...     repr(Event(field='x'))
        "Event({'field': 'x', 'timestamp': datetime.datetime(2013, 1, 1, 2, 34, 56)})"
        """
        # pprint returns a stable ordering for tests
        return 'Event(%s)' % pformat(dict(self))
