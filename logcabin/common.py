import logging
import gevent
from gevent.queue import JoinableQueue
import gevent.monkey
gevent.monkey.patch_thread()
import threading
from context import Context, ContextManager

# Yuck - workaround python 2.7 bug:
# http://stackoverflow.com/questions/13193278/understand-python-threading-bug
threading._DummyThread._Thread__stop = lambda x: 42

class Stage(object):
    """Base class for all stages.

    Common parameters to all stages:
    :param string on_error: 'tag' or 'reject' - determines behaviour on error (default: reject)
    """

    def __init__(self, on_error='reject'):
        # self.input = input
        # self.output = output
        self.logger = logging.getLogger(type(self).__name__)
        self.busy = threading.Lock()
        self.on_error = on_error
        self.register()

    def __str__(self):
        return type(self).__name__

    def register(self):
        Context.instance.current().add(self)

    def setup(self, q):
        self.output = q
        self.input = JoinableQueue()
        return self.input

    def configure(self):
        """Configure the stage"""
        pass

    def start(self):
        """Start the stage running in a greenlet."""
        # run each in a greenlet
        self.g = gevent.spawn(self._run)

    def _run(self):
        pass

    def _error(self, event, reason=None):
        if self.on_error == 'tag':
            event.add_tag('_unparsed')
            if reason:
                event['message'] = str(reason)
            self.output.put(event)
        else:
            # otherwise ignore
            self.logger.warn('ignoring %s: %s' % (event, reason))

    def stop(self):
        """Stop the stage from running."""
        # if necesssary, avoid to more gracefully handle termination in the stage
        with self.busy:
            self.g.kill()
            self.g.join()
        self.logger.debug('Stopped')

class SimpleStage(Stage):
    def _run(self):
        while True:
            event = self.input.get()

            # block exit whilst processing an event
            with self.busy:
                ret = self.process(event)
                if ret is not False and self.output:
                    self.output.put(event)

    def process(self, event):
        pass

class MultiStage(Stage, ContextManager):
    def __init__(self):
        self.stages = []
        super(MultiStage, self).__init__()

    def __str__(self):
        x = ', '.join(str(s) for s in self.stages)
        return '%s(%s)' % (type(self).__name__, x)

    def add(self, stage):
        """Add this stage to the list"""
        self.stages.append(stage)

    def start(self):
        """Spawn the greenlets for all the inputs, filters and outputs."""
        for s in self.stages:
            self.logger.debug('Starting %s' % s)
            s.start()
            self.logger.debug('Started %s' % s)

    def stop(self):
        """Stop all the inputs, filters and outputs."""
        for s in self.stages:
            self.logger.debug('Stopping %s' % s)
            s.stop()
            self.logger.debug('Stopped %s' % s)

class Constants(object):
    ISOFORMAT = '%Y-%m-%dT%H:%M:%SZ'
