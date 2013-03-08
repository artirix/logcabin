import time
import gevent

from .output import Output

class Perf(Output):
    """Simple performance counter output.

    :param integer period: interval between reports in seconds
    """
    def __init__(self, period=60):
        super(Perf, self).__init__()
        self.period = period
        self.now = time.time()
        self.count = 0

    def start(self):
        super(Perf, self).start()

        # spawn additional greenlet to do periodic reporting
        gevent.spawn(self._report)

    def _report(self):
        while True:
            gevent.sleep(self.period)

            now = time.time()
            if self.count > 0:
                self.logger.info('%d in %ds (%.1f/s)' % (
                    self.count, now-self.now, self.count/(now-self.now)))
            self.now = now
            self.count = 0

    def process(self, event):
        self.count += 1
