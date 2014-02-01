from .output import Output
import os
import gevent
import subprocess
import datetime
from ..event import Event
from ..util import Periodic

class File(Output):
    """Log to file.

    The file format is a line per event as json.

    When a log is rolled, a 'virtual' event will be generated with the tag
    'fileroll', and the field 'filename' which can be used by further outputs to
    process a log file when it rolls (eg. batch upload to S3). This event contains
    a 'trigger' field containing the original event that caused the log roll.

    :param string filename: the log filename (required). You can use event
      format values in this (eg. 'output-{program}.log')
    :param integer max_size: maximum size of file before rolling to .1, .2, etc.
    :param integer max_count: maximum number of rolled files (default: 10)
    :param string compress: set to 'gz' to compress the file after rolling.

    Example::

        File(filename='mylogs.log', max_size=10, compress='gz')
    """
    def __init__(self, filename, max_size=None, max_count=10, compress=None):
        super(File, self).__init__()
        self.filename = filename
        self.max_size = max_size
        self.max_count = max_count
        if compress is True:
            compress = 'gz'
        elif compress is None:
            compress = False
        assert compress in (False, 'gz',)
        self.compress = compress
        self.last_filename = None
        self.last_event = None

        if 'timestamp' in self.filename:
            # if the log file name is timestamped, periodically check if it has
            # rolled over.
            self.periodic = Periodic(30, self._check_rotate)
        else:
            self.periodic = None

    def _check_rotate(self):
        now = datetime.datetime.utcnow()
        filename = self.filename.format(timestamp=now)
        if self.last_filename and filename != self.last_filename:
            self._rotate(self.last_filename, self.last_event, self.last_event)
            self.last_filename = filename 

    def start(self):
        super(File, self).start()
        if self.periodic is not None:
            self.periodic.start()

    def stop(self):
        if self.periodic is not None:
            self.periodic.kill()
            self.periodic.join()
        super(File, self).stop()

    def process(self, event):
        filename = event.format(self.filename)
        if self.max_size and os.path.exists(filename) and os.path.getsize(filename) > self.max_size:
            self._rotate(filename, self.last_event, event)

        if 'timestamp' in self.filename and self.last_filename != filename:
            if self.last_filename:
                # file has rolled by timestamp
                self._rotate(self.last_filename, self.last_event, event)
            self.last_filename = filename
        self.last_event = event

        dirname = os.path.dirname(filename)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        with file(filename, 'a') as fout:
            d = event.to_json()
            self.logger.debug('Writing to %s: %s' % (filename, d))
            print >>fout, d

    def _rotate(self, filename, last, trigger):
        if not os.path.exists(filename):
            return

        suffix = ''
        if self.compress == 'gz':
            suffix = '.'+self.compress

        roll_first = filename+'.1'+suffix
        renames = [(filename, roll_first)]
        self.logger.info('Rotating logfile %s to %s' % (filename, roll_first))
        for n, (oldname, newname) in enumerate(renames):
            if self.max_count and n == self.max_count-1:
                # cap renamed files if max_count specified
                break

            if os.path.exists(newname):
                base, num = newname.strip(suffix).rsplit('.', 1)
                renames.append((newname, '%s.%s%s' % (base, int(num)+1, suffix)))

        if suffix:
            # actually a rename, then compress
            renames[0] = (filename, filename+'.1')

        for oldname, newname in reversed(renames):
            self.logger.debug('Renaming logfile %s->%s' % (oldname, newname))
            os.rename(oldname, newname)

        if self.compress == 'gz':
            self._gz(filename+'.1')

        # emit 'virtual' event for rolled log file
        self.output.put(Event(tags=['fileroll'], filename=roll_first, last=last or trigger, trigger=trigger))

    def _gz(self, filename):
        self.logger.debug('Gzipping %s' % (filename,))
        ps = subprocess.Popen(['gzip', filename])
        while ps.poll() is None:
            gevent.sleep(0.01)
