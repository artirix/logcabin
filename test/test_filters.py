from unittest import TestCase
import gevent
from gevent.queue import Queue
import datetime
import mock

from logcabin.event import Event
from logcabin.context import DummyContext
from logcabin.filters import json, mutate, python, regex, stats, syslog, url

from testhelper import assertEventEquals, about, between

class FilterTests(TestCase):
    def create_stage(self, **conf):
        return self.cls(**conf)

    def create(self, conf={}, events=[]):
        self.input = Queue()
        self.output = Queue()
        with DummyContext():
            self.i = self.create_stage(**conf)
        self.input = self.i.setup(self.output)

        self.i.start()
        for ev in events:
            self.input.put(ev)
        return self.i

    def wait(self, timeout=1.0, events=1):
        with gevent.Timeout(timeout):
            # wait for input to be consumed and output to be produced
            while self.input.qsize():
                gevent.sleep(0.0)
            while self.output.qsize() < events:
                gevent.sleep(0.0)

        if events:
            return [self.output.get() for n in xrange(events)]

    def tearDown(self):
        self.i.stop()

class JsonTests(FilterTests):
    cls = json.Json

    def test_consume(self):
        self.create({},
            [Event(data='{"a": 1}')])
        q = self.wait()
        assertEventEquals(self, Event(a=1), q[0])

    def test_consume_false(self):
        self.create({'consume': False},
            [Event(data='{"a": 1}')])
        q = self.wait()
        assertEventEquals(self, Event(a=1, data='{"a": 1}'), q[0])

    def test_bad_json(self):
        self.create({'consume': False},
            [Event(data='"invalid')])
        self.wait(events=0)
        self.assertEquals(0, self.output.qsize())

class RegexTests(FilterTests):
    cls = regex.Regex

    def test_match(self):
        self.create({'regex': r'(?P<letters>[a-z]+)(?P<numbers>\d+)'},
            [Event(data='abc123')])
        q = self.wait()
        assertEventEquals(self, Event(letters='abc', numbers='123'), q[0])

    def test_no_match(self):
        self.create({'regex': r'(?P<letters>[a-z]+)(?P<numbers>\d+)',
            'on_error': 'tag'},
            [Event(data='.!$#')])
        q = self.wait()
        self.assertEquals(['error'], q[0].tags)

class MutateTests(FilterTests):
    cls = mutate.Mutate

    def test_set(self):
        self.create({'set': {'a': 2}},
            [Event(a=1)])
        q = self.wait()
        assertEventEquals(self, Event(a=2), q[0])

    def test_set_format(self):
        self.create({'set': {'a': '{b}.{c}'}},
            [Event(b=1, c=2)])
        q = self.wait()
        assertEventEquals(self, Event(a='1.2', b=1, c=2), q[0])

    def test_rename(self):
        self.create({'rename': {'b': 'a', 'd': 'c'}},
            [Event(a=1)])
        q = self.wait()
        assertEventEquals(self, Event(b=1), q[0])

    def test_copy(self):
        self.create({'copy': {'b': 'a', 'd': 'c'}},
            [Event(a=1, c=5)])
        q = self.wait()
        assertEventEquals(self, Event(b=1, a=1, c=5, d=5), q[0])

    def test_unset(self):
        self.create({'unset': ['a', 'c']},
            [Event(a=1, b=2)])
        q = self.wait()
        assertEventEquals(self, Event(b=2), q[0])

class PythonTests(FilterTests):
    cls = python.Python

    def test_simple(self):
        function = mock.Mock()
        ev = Event(data='abc123')
        self.create({'function': function},
            [ev])
        q = self.wait()
        
        assertEventEquals(self, Event(data='abc123'), q[0])
        function.assert_called_with(ev)

class UrlTests(FilterTests):
    cls = url.Url

    def test_match(self):
        self.create({'field': 'data'},
            [Event(data='abc?a=1%2C2&b=2+3')])
        q = self.wait()
        assertEventEquals(self, Event(path='abc', a='1,2', b='2 3'), q[0])

    def test_no_match(self):
        self.create({'field': 'data',
            'on_error': 'tag'},
            [Event(data=None)])
        q = self.wait()
        self.assertEquals(['error'], q[0].tags)

class StatsTests(FilterTests):
    cls = stats.Stats

    events = [
        Event(controller='home', action='index', duration=3.0, bytes=6926, timings={'view': 1.0}),
        Event(controller='home', action='login', duration=2.4, bytes=15568, timings={'view': 2.0}),
        Event(controller='home', action='index', duration=4.0, bytes=18150, timings={'view': 1.2}),
        Event(controller='home', action='index', duration=3.5, bytes=30159, timings={'view': 2.3}),
        Event(controller='missing', action='duration'),
        Event(someotherevent='blah', duration=3.5),
    ]

    def test_nested(self):
        self.create({'period': 0.1, 'metrics': {'rails.{controller}.{action}.{0}': 'timings.*'}},
            self.events)

        # 8 events expected - the above 6, and then 2 stat events
        q = self.wait(events=8)

        q = [i for i in q if i.stats]
        q.sort(key=lambda k: k.metric)

        expected = Event(metric='rails.home.index.timings.view',
            stats={
                'count': 3,
                'max': 2.3,
                'mean': 1.5,
                'median': 1.2,
                'min': 1.0,
                'rate': between(1, 100),
                'stddev': about(2.34, 2),
                'upper95': 2.19,
                'upper99': 2.278},
            tags=['stat'],
        )
        assertEventEquals(self, expected, q[0])

        expected = Event(metric='rails.home.login.timings.view',
            stats={
                'count': 1,
                'max': 2.0,
                'mean': 2.0,
                'median': 2.0,
                'min': 2.0,
                'rate': between(1, 100),
                'stddev': 0.0,
                'upper95': 2.0,
                'upper99': 2.0},
            tags=['stat'],
        )
        assertEventEquals(self, expected, q[1])

        # wait for further two 'zero' stats
        q = self.wait(events=2)

    def test_wildcard(self):
        self.create({'period': 0.1, 'metrics': {'rails.{controller}.{action}.{0}': '*'}},
            self.events)

        # 8 events expected - the above 6, and then 4 stat events
        q = self.wait(events=10)

        q = [i for i in q if i.stats]
        q.sort(key=lambda k: k.metric)

        expected = Event(metric='rails.home.index.bytes',
            stats={
                'count': 3,
                'rate': between(1, 100),
                'max': 30159,
                'min': 6926,
                'median': 18150,
                'mean': 18411,
                'stddev': about(30789),
                'upper95': 28958.1,
                'upper99': 29918.82,
            },
            tags=['stat'],
        )
        assertEventEquals(self, expected, q[0])

        expected = Event(metric='rails.home.index.duration',
            stats={
                'count': 3,
                'rate': between(1, 100),
                'max': 4.0,
                'min': 3.0,
                'median': 3.5,
                'mean': 3.5,
                'stddev': 5.0,
                'upper95': 3.95,
                'upper99': 3.99,
            },
            tags=['stat'],
        )
        assertEventEquals(self, expected, q[1])

        expected = Event(metric='rails.home.login.duration',
            stats={
                'count': 1,
                'rate': between(1, 100),
                'max': 2.4,
                'min': 2.4,
                'median': 2.4,
                'mean': 2.4,
                'stddev': 0.0,
                'upper95': 2.4,
                'upper99': 2.4,
            },
            tags=['stat'],
        )
        assertEventEquals(self, expected, q[3])

class SyslogTests(FilterTests):
    cls = syslog.Syslog

    # Formats - you can never have enough of them!
    good_packets = [
        '<174>Nov 30 19:56:13 host01 prog[1234]: log message', # RSYSLOG_ForwardFormat
        '<174>Mar  4 11:57:46 micro01 testlog.py: test', # RSYSLOG_TraditionalFileFormat
        '<174>2012-12-07T13:44:27.710956+01:00 test01 program: test' # RSYSLOG_ForwardFormat
    ]
    good_events = [
        Event(
            timestamp=datetime.datetime(2013, 10, 30, 19, 56, 13),
            facility='local5',
            severity='Informational',
            host='host01',
            program='prog',
            pid='1234',
            message='log message'),
        Event(
            timestamp=datetime.datetime(2013, 3, 4, 11, 56, 46),
            facility='local5',
            severity='Informational',
            host='micro01',
            program='testlog.py',
            pid=None,
            message='test'),
        Event(
            timestamp=datetime.datetime(2012, 12, 7, 12, 44, 27, 710956),
            facility='local5',
            severity='Informational',
            host='test01',
            program='program',
            pid=None,
            message='test')

    ]
    bad_packets = ['<>Nov 30 19:56:13 host01 prog[1234]: log message']

    def test_good(self):
        self.create({},
            [Event(data=x) for x in self.good_packets])

        events = self.wait(events=len(self.good_events))
        for ev in self.good_events:
            assertEventEquals(self, ev, events.pop(0))

    def test_bad(self):
        self.create({'consume': False, 'on_error': 'tag'},
            [Event(data=x) for x in self.bad_packets])
        events = self.wait(events=len(self.bad_packets))

        bad_events = [Event(data=x, message='invalid syslog', tags=['error']) for x in self.bad_packets]
        for ev in bad_events:
            assertEventEquals(self, ev, events.pop(0))
