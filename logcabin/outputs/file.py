from .output import Output
import os
import gevent
import subprocess
from ..event import Event

class File(Output):
    """Log to file.

    The file format is a line per event as json.

    When a log is rolled, a 'virtual' event will be generated with the tag
    'fileroll', and the field 'filename' which can be used by further outputs to
    process a log file when it rolls (eg. batch upload to S3).

    :param string filename: the log filename (required). You can use event
      format values in this (eg. 'output-{program}.log')
    :param integer max_size: maximum size of file before rolling to .1, .2, etc.
    :param integer max_count: maximum number of rolled files (default: 10)
    :param string compress: set to 'gz' to compress the file after rolling.
    """
    def __init__(self, filename, max_size=None, max_count=10, compress=None):
        super(File, self).__init__()
        self.filename = filename
        self.max_size = max_size
        self.max_count = max_count
        self.compress = compress

    def process(self, event):
        filename = event.format(self.filename)
        if self.max_size and os.path.exists(filename) and os.path.getsize(filename) > self.max_size:
            self._rotate(filename)

        with file(filename, 'a') as fout:
            print >>fout, event.to_json()

    def _rotate(self, filename):
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
        self.output.put(Event(tags=['fileroll'], filename=roll_first))

    def _gz(self, filename):
        self.logger.debug('Gzipping %s' % (filename,))
        ps = subprocess.Popen(['gzip', filename])
        while ps.poll() is None:
            gevent.sleep()
