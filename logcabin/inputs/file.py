import gevent.select
import subprocess
import glob

from ..event import Event
from .input import Input

class File(Input):
    """Tails events from a log file on disk.

    Creates events with the field 'data' set to the line received.

    :param string path: path on the file system to the log file(s), wildcards may
      be used to match multiple files.
    """

    def __init__(self, path):
        super(File, self).__init__()
        self.path = path

    def _run(self):
        # Nice to haves: gevent.subprocess in 1.0

        # This approach is simple but dumb, and has its limitations:
        # - we don't find new files appearing later that match the wildcard
        # - we persist state and pick up file position where we left off
        args = ['tail', '-F']
        paths = glob.glob(self.path)
        if paths:
            # seek to end
            args.append('-n0')
        while not paths:
            gevent.sleep(0.01)
            paths = glob.glob(self.path)

        self.logger.debug('Tailing %s' % ', '.join(paths))
        ps = subprocess.Popen(args + paths,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        while True:
            gevent.select.select([ps.stdout], [], [])
            data = ps.stdout.readline()
            if data:
                if data.endswith('\n'):
                    data = data[0:-1]
                self.logger.debug('Received: %r' % data)
                self.output.put(Event(data=data))
