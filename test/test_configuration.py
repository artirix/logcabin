from unittest import TestCase

from logcabin.configuration import PyConfigLoader, ConfigException

import os

def _p(p):
    return os.path.join(os.path.dirname(__file__), p)

class PyConfigLoaderTests(TestCase):
    def test_good(self):
        loader = PyConfigLoader(_p('config/good.py'))
        loader.configure()
        pipeline = loader.pipeline

        # kick the tyres
        pipeline.start()
        pipeline.stop()

    def test_complex(self):
        loader = PyConfigLoader(_p('config/complex.py'))
        loader.configure()
        pipeline = loader.pipeline

        # kick the tyres
        pipeline.start()
        import gevent
        gevent.sleep()
        pipeline.stop()

    def test_bad(self):
        loader = PyConfigLoader(_p('test/config/bad.py'))
        self.assertRaises(ConfigException, loader.configure)
