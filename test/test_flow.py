from unittest import TestCase
import gevent
from gevent.queue import Queue

from logcabin.event import Event
from logcabin.context import Context, DummyContext
from logcabin.flow import If, Switch, Sequence
from logcabin.filters import mutate

from testhelper import assertEventEquals

class FlowTests(TestCase):
    def create(self, conf={}, events=[]):
        self.input = Queue()
        self.output = Queue()

        context = DummyContext()
        with context:
            self.i = self.create_stage(**conf)
            self.input = self.i.setup(self.output)

        self.assertEquals(1, len(context.stages))

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

        self.i.stop()
        if events:
            return [self.output.get() for n in xrange(events)]

class SequenceTests(FlowTests):
    def create_stage(self):
        with Sequence() as test:
            mutate.Mutate(set={'a': 1})
            mutate.Mutate(set={'b': 2})
        return test

    def test_simple(self):
        self.create({},
            [Event(a=1)])
        q = self.wait()
        assertEventEquals(self, Event(a=1, b=2), q[0])

class SwitchTests(FlowTests):
    def create_stage(self):
        with Switch() as test:
            with test(lambda ev: ev.a == 1):
                mutate.Mutate(set={'b': 1})
            with test('a == 2'):
                mutate.Mutate(set={'b': 2})
            with test.default:
                mutate.Mutate(set={'b': False})
        return test

    def test_lambda(self):
        self.create({},
            [Event(a=1)])
        q = self.wait()
        assertEventEquals(self, Event(a=1, b=1), q[0])

    def test_snippet(self):
        self.create({},
            [Event(a=2)])
        q = self.wait()
        assertEventEquals(self, Event(a=2, b=2), q[0])

    def test_default(self):
        self.create({},
            [Event(a=3)])
        q = self.wait()
        assertEventEquals(self, Event(a=3, b=False), q[0])

    def test_missing(self):
        self.create({},
            [Event()])
        q = self.wait()
        assertEventEquals(self, Event(b=False), q[0])

class IfTests(FlowTests):
    def create_stage(self):
        test = If(lambda ev: ev.a == 1)
        with test:
            mutate.Mutate(set={'b': 1})
        return test

    def test_true(self):
        self.create({},
            [Event(a=1)])
        q = self.wait()
        assertEventEquals(self, Event(a=1, b=1), q[0])

    def test_false(self):
        self.create({},
            [Event(a=2)])
        q = self.wait()
        assertEventEquals(self, Event(a=2), q[0])
