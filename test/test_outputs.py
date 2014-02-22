from unittest import TestCase
import gevent
from gevent.queue import Queue
import gevent.server
import mock
import json
import gzip
import os
import random
import struct
import time
from datetime import datetime
import cPickle as pickle
import zmq.green as zmq
import urllib2

from logcabin.event import Event
from logcabin.context import DummyContext

from logcabin.outputs import elasticsearch, file as fileoutput, graphite, log, \
    mongodb, perf, s3, zeromq

from testhelper import TempDirectory, assertEventEquals, ANY

class OutputTests(TestCase):
    def create(self, conf={}):
        with DummyContext():
            self.i = i = self.cls(**conf)
        self.output = Queue()
        self.input = i.setup(self.output)
        i.start()
        return i

    def waitForEmpty(self, timeout=1.0):
        with gevent.Timeout(timeout):
            while self.input.qsize():
                gevent.sleep()

    def tearDown(self):
        self.i.stop()

class LogTests(OutputTests):
    cls = log.Log

    def test_log(self):
        self.create()

        self.input.put(Event(field='x'))
        self.waitForEmpty()

        self.assertEquals(0, self.input.qsize())

class ElasticsearchTests(OutputTests):
    cls = elasticsearch.Elasticsearch

    def test_log(self):
        with mock.patch('urllib2.urlopen') as urlopen_mock:
            urlopen_mock.return_value.read.return_value = json.dumps({'_type': 'event', '_id': 'w0HnGYHFSOS7EBIWnxBcEg', '_version': 1, '_index': 'test'})
            i = self.create({'index': 'test', 'type': 'event'})

            self.input.put(Event(field='x'))
            self.waitForEmpty()
            i.stop()

            urlopen_mock.assert_called_once_with('http://localhost:9200/test/event/', data=ANY)

    def test_400_bad_request(self):
        with mock.patch('urllib2.urlopen') as urlopen_mock:
            def raise_400(url, data):
                raise urllib2.HTTPError(url, 400, "Bad Request", {}, None)
            urlopen_mock.side_effect = raise_400
            i = self.create({'index': 'test', 'type': 'event'})

            self.input.put(Event(field='x'))
            self.waitForEmpty()
            i.stop()

            urlopen_mock.assert_called_once_with(ANY, data=ANY)

    def test_empty_type(self):
        with mock.patch('urllib2.urlopen') as urlopen_mock:
            urlopen_mock.return_value.read.return_value = json.dumps({'_type': 'event', '_id': 'w0HnGYHFSOS7EBIWnxBcEg', 'ok': True, '_version': 1, '_index': 'test'})
            i = self.create({'index': 'test', 'type': ''})

            self.input.put(Event(field='x'))
            self.waitForEmpty()
            i.stop()

            self.failIf(urlopen_mock.called)

class FileTests(OutputTests):
    cls = fileoutput.File

    def assertFileContents(self, expected, filename):
        if filename.endswith('.gz'):
            actual = gzip.open(filename).read()
        else:
            actual = file(filename).read()

        self.assertEquals(expected, actual)

    events = [Event(program='httpd'), Event(program='ntpd')]

    def test_simple(self):
        with TempDirectory():
            self.create({'filename': 'log/output_{program}.log'})

            map(self.input.put, self.events)
            self.waitForEmpty()

            self.assertFileContents(self.events[0].to_json()+'\n', 'log/output_httpd.log')
            self.assertFileContents(self.events[1].to_json()+'\n', 'log/output_ntpd.log')

    def test_max_size(self):
        with TempDirectory():
            self.create({'filename': 'output.log',
                'max_size': 16})

            map(self.input.put, self.events)
            self.waitForEmpty()

            self.assertFileContents(self.events[0].to_json()+'\n', 'output.log.1')
            self.assertFileContents(self.events[1].to_json()+'\n', 'output.log')

            # assert the 'fileroll' event is generated
            self.assert_(self.output.qsize())
            events = [self.output.get() for i in xrange(self.output.qsize())]
            assertEventEquals(self, Event(tags=['fileroll'], filename='output.log.1', last=self.events[0], trigger=self.events[1]), events[1])

    def test_timestamped(self):
        events = [
            Event(message='1', timestamp=datetime(2013, 1, 1, 23, 59, 58)),
            Event(message='2', timestamp=datetime(2013, 1, 1, 23, 59, 59)),
            Event(message='3', timestamp=datetime(2013, 1, 2, 0, 0, 0)),
            Event(message='4', timestamp=datetime(2013, 1, 2, 0, 0, 1))]

        with TempDirectory():
            self.create({'filename': 'output-{timestamp:%Y%m%d}.log',
                'compress': 'gz'})

            map(self.input.put, events)
            self.waitForEmpty()

            self.assertFileContents(events[0].to_json()+'\n'+events[1].to_json()+'\n', 'output-20130101.log.1.gz')
            self.assertFileContents(events[2].to_json()+'\n'+events[3].to_json()+'\n', 'output-20130102.log')

            # assert the 'fileroll' event is generated
            self.assertEquals(len(events)+1, self.output.qsize())
            outputs = [self.output.get() for i in xrange(self.output.qsize())]
            assertEventEquals(self, Event(tags=['fileroll'], filename='output-20130101.log.1.gz', last=events[1], trigger=events[2]), outputs[2])

    def test_compress(self):
        with TempDirectory():
            self.create({'filename': 'output.log',
                'max_size': 16,
                'compress': 'gz'})

            map(self.input.put, self.events)
            self.waitForEmpty()
            self.i.stop()

            self.assertFileContents(self.events[0].to_json()+'\n', 'output.log.1.gz')
            self.assertFileContents(self.events[1].to_json()+'\n', 'output.log')

    def test_max_count(self):
        with TempDirectory():
            self.create({'filename': 'output.log',
                'max_size': 16,
                'max_count': 2})

            map(self.input.put, self.events * 10)
            self.waitForEmpty()

            self.assertFileContents(self.events[1].to_json()+'\n', 'output.log')
            self.assert_(not os.path.exists('output.log.3'))

class PerfTests(OutputTests):
    cls = perf.Perf

    def test_log(self):
        self.create()

        self.input.put(Event(field='x'))
        self.waitForEmpty()

        self.assertEquals(0, self.input.qsize())

class MongodbTests(OutputTests):
    cls = mongodb.Mongodb

    @mock.patch('pymongo.MongoClient')
    def test_log(self, mock_client):
        mock_db = mock_client.return_value.__getitem__ = mock.Mock()
        mock_col = mock_db.return_value.__getitem__ = mock.Mock()
        mock_col.return_value.insert.return_value = 'abc123' # mock id return

        self.create()

        self.input.put(Event(field='x'))
        self.waitForEmpty()

        self.assertEquals(0, self.input.qsize())

class S3Tests(OutputTests):
    cls = s3.S3

    @mock.patch('boto.connect_s3')
    def test_upload(self, mock_s3):
        mock_conn = mock_s3.return_value
        mock_bucket = mock_conn.get_bucket.return_value
        mock_key = mock_bucket.new_key.return_value

        with TempDirectory():
            # create log file for it to upload
            with file('output.log', 'w') as fout:
                fout.write('a log file')

            self.create({'access_key': 'dummy', 'secret_key': 'dummy',
                'bucket': 'bucket1', 'path': 'logs/1.json'})
            self.input.put(Event(tags=['fileroll'], filename='output.log'))
            self.waitForEmpty()

        mock_s3.assert_called_with('dummy', 'dummy')
        mock_conn.get_bucket.assert_called_with('bucket1')
        mock_bucket.new_key.assert_called_with('logs/1.json')
        mock_key.set_contents_from_filename.assert_called_with('output.log')

class GraphiteTests(OutputTests):
    cls = graphite.Graphite

    @mock.patch('logcabin.event.datetime')
    def test_log(self, mock_datetime):
        now = datetime(2013, 1, 1, 2, 34, 56, 789012)
        t_now = int(time.mktime(now.timetuple()))
        mock_datetime.utcnow.side_effect = lambda: now

        port = random.randint(1024, 65535)
        received = []
        
        def handle(socket, address):
            # graphite is a 4-byte length, followed by pickled representation
            length, = struct.unpack('!L', socket.recv(4))
            d = socket.recv(length)
            received.append(pickle.loads(d))
        server = gevent.server.StreamServer(('', port), handle)
        server.start()

        self.create({'port': port})

        self.input.put(Event(metric='a.b.c', stats={'mean': 1.5, 'min': 1.0}))
        self.waitForEmpty()
        self.i.stop()

        self.assertEquals(0, self.input.qsize())
        server.stop()
        self.assertEquals(1, len(received))
        self.assertEquals([
            ('a.b.c.min', (t_now, 1.0)),
            ('a.b.c.mean', (t_now, 1.5))
        ], received[0])

    def test_unavailable(self):
        port = random.randint(1024, 65535)
        received = []
        
        def handle(socket, address):
            # graphite is a 4-byte length, followed by pickled representation
            length, = struct.unpack('!L', socket.recv(4))
            d = socket.recv(length)
            received.append(pickle.loads(d))
        server = gevent.server.StreamServer(('', port), handle)

        self.create({'port': port})

        self.input.put(Event(metric='a.b.c', stats={'mean': 1.5, 'min': 1.0}))
        server.start()

        self.waitForEmpty()

        self.assertEquals(0, self.input.qsize())
        self.i.stop()
        server.stop()
        self.assertEquals(1, len(received))

class ZeromqTests(OutputTests):
    cls = zeromq.Zeromq

    def test_log(self):
        conf = {'address': 'ipc://testipc2', 'mode': 'connect', 'socket': 'PUSH'}
        self.create(conf)

        # create a zeromq socket
        ctx = zmq.Context()
        sock = ctx.socket(zmq.PULL)
        sock.bind(conf['address'])

        ev = Event(field='x')
        self.input.put(ev)
        self.waitForEmpty()

        data = sock.recv()
        self.assertEquals(ev.to_json(), data)
