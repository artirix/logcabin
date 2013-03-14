from unittest import TestCase
import zmq.green as zmq
import gevent
import gevent.socket as socket
from gevent.queue import Queue
import random

from logcabin.event import Event
from logcabin.context import DummyContext
from logcabin.inputs import udp, zeromq, file as fileinput

from testhelper import TempDirectory, assertEventEquals

class InputTests(TestCase):
    def create(self, conf):
        self.output = Queue()
        with DummyContext():
            self.i = i = self.cls(**conf)
        i.setup(self.output)
        i.start()
        return i

    def waitForQueue(self, timeout=1.0, events=1):
        with gevent.Timeout(timeout):
            while self.output.qsize() < events:
                gevent.sleep(0.0)

        self.i.stop()
        if events:
            return [self.output.get() for n in xrange(events)]

class ZeromqTests(InputTests):
    cls = zeromq.Zeromq

    def test_event(self):
        conf = {'address': 'ipc://testipc'}
        self.create(conf)

        # create a zeromq socket
        ctx = zmq.Context()
        sock = ctx.socket(zmq.PUSH)
        sock.connect(conf['address'])
        sock.send('abc')

        q = self.waitForQueue()
        assertEventEquals(self, Event(data='abc'), q[0])

class UdpTests(InputTests):
    cls = udp.Udp

    def test_event(self):
        conf = {'port': random.randint(1024, 65535)}
        self.create(conf)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.sendto('abc', ('', conf['port']))

        # yield for processing to happen
        q = self.waitForQueue()
        assertEventEquals(self, Event(data='abc'), q[0])

class FileTests(InputTests):
    cls = fileinput.File

    def test_success(self):
        with TempDirectory():
            conf = {'path': 'test*.log'}
            self.create(conf)

            # create log after a short time
            gevent.sleep(0.01)
            with file('test1.log', 'w') as fin:
                print >>fin, 'abc'
                gevent.sleep(0.01)
                print >>fin, 'def'

            q = self.waitForQueue(events=2)
            assertEventEquals(self, Event(data='abc'), q[0])
            assertEventEquals(self, Event(data='def'), q[1])

    def test_missing(self):
        with TempDirectory():
            conf = {'path': 'test*.log'}
            self.create(conf)

            self.waitForQueue(events=0)
