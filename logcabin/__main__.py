#!/usr/bin/env python

import logcabin
import sys
import os
import json
import gevent
import gevent.event
import gevent.monkey
gevent.monkey.patch_all()
import logging
import logging.config
import signal
import optparse
from util import ConfigException
from configuration import PyConfigLoader

class LogCabin(object):
    """Main application object"""

    def setup(self):
        """Application setup"""
        self._setup_args()
        self._setup_logging()
        self._setup_config()
        self._setup_signals()

    def _setup_logging(self):
        # configure logging
        logging.config.dictConfig(self.logconfig)
        self.logger = logging.getLogger('main')

    def _setup_config(self):
        # load configuration
        self.config = PyConfigLoader(self.opts.config)
        self.config.configure()
        self.pipeline = self.config.pipeline

    def _setup_args(self):
        parser = optparse.OptionParser()
        parser.add_option('-v', '--verbose', action='store_true', help='Verbose logging (debug)')
        parser.add_option('-l', '--log', help='Log to the given log file', default='logcabin.log')
        parser.add_option('-c', '--config', help='Configuration file to use', default='config.py')
        opts, args = parser.parse_args()

        # logging configuration
        logging_cfg = os.path.join(os.path.dirname(__file__), 'logging.cfg')
        self.logconfig = json.load(file(logging_cfg))
        logpath = os.path.abspath(opts.log)
        self.logconfig['handlers']['file']['filename'] = logpath

        if opts.verbose:
            # output to console at DEBUG too
            root = self.logconfig['loggers']['']
            root['handlers'].append('console')
            root['level'] = 'DEBUG'
        else:
            print 'Logging to %s' % logpath

        self.opts = opts

    def _setup_signals(self):
        self.shutdown = gevent.event.Event()
        gevent.signal(signal.SIGTERM, self._signal, 'SIGTERM')
        gevent.signal(signal.SIGINT, self._signal, 'SIGINT')

    def _signal(self, name):
        self.logger.info('%s received, shutting down' % name)
        self.shutdown.set()

    def start(self):
        """Start the pipeline."""
        self.pipeline.start()
        self.logger.info('Started pipeline: %s' % self.pipeline)

    def stop(self):
        """Stop the pipeline."""
        self.logger.info('Stopping pipeline')
        self.pipeline.stop()

    def run(self):
        """Run the whole application, then wait on termination by signal."""
        try:
            self.setup()
        except ConfigException as ex:
            self.logger.error(str(ex))
            print >>sys.stderr, str(ex)
            return False

        self.start()
        self.shutdown.wait()
        self.stop()

        self.logger.info('Shutdown complete')
        return True


if __name__ == '__main__':
    logcabin.main()
