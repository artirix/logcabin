import sys
import logging

from pipeline import Pipeline

class ConfigException(Exception):
    pass

class PyConfigLoader(object):
    def __init__(self, path):
        self.logger = logging.getLogger('config')
        self.path = path

    def configure(self):
        self.logger.info('Loading configuration: %r' % self.path)
        # push implicit top-level context
        self.pipeline = Pipeline()
        with self.pipeline:
            try:
                execfile(self.path)
            except Exception as ex:
                trace = sys.exc_info()[2]
                raise ConfigException(ex), None, trace

        # pipeline has no final output queue
        self.pipeline.setup(None)
