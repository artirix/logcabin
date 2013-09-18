import gevent
import os
import glob
import logging
import errno

from ..event import Event
from .input import Input
from gevent.queue import JoinableQueue

class Tail(gevent.Greenlet):
    """Asynchronously tails a file by name, delivering new lines to a queue."""
    def __init__(self, path, queue, statedir):
        super(Tail, self).__init__()
        self.logger = logging.getLogger('Tail')
        self.path = path
        if statedir:
            self.offset_path = os.path.join(statedir, self.path.replace('/', '_') + '.offset')
        else:
            self.offset_path = self.path + '.offset'
        self.queue = queue
        self.fin = None
        self.start()

    def _run(self):
        try:
            self.tail()
        except:
            self._write_state_file()
            if self.fin:
                self.logger.debug('Closed: %s' % self.path)
                self.fin.close()

    def _write_state_file(self):
        with file(self.offset_path, 'w') as fout:
            offset = self.fin.tell()
            self.logger.debug("Writing state file: %s at offset %d" % (self.offset_path, offset))
            print >>fout, offset

    def tail(self):
        self._ensure_open()
        if os.path.exists(self.offset_path):
            offset = file(self.offset_path).read()
            offset = int(offset)
            self.logger.debug("Seeking in %s to %d" % (self.path, offset))
            self.fin.seek(offset)

        last_st = None

        while True:
            try:
                st = os.stat(self.path)
            except OSError as ex:
                # ignore "No such file"
                if ex.errno != errno.ENOENT:
                    raise
                st = None

            if st == last_st:
                gevent.sleep(0.2)
                continue

            # read pending lines
            line = self.fin.readline()
            while line:
                self.queue.put(line)
                line = self.fin.readline()

            # check for file rolling
            if not st or (last_st and st.st_ino != last_st.st_ino):
                # file has rolled, close and open again
                self.logger.debug('Detected roll: %s' % self.path)
                self._ensure_open()
                st = None # restart
            elif st and last_st and st.st_size < last_st.st_size:
                self.logger.debug('Detected truncation: %s' % self.path)
                self._ensure_open()
                st = None # restart

            last_st = st

    def _ensure_open(self):
        if self.fin:
            self.fin.close()
            self.fin = None

        while True:
            try:
                self.fin = file(self.path, 'r')
                self.logger.debug('Opened: %s' % self.path)
                return
            except IOError as ex:
                if ex.errno == errno.ENOENT:
                    gevent.sleep(0.01)
                    continue
                raise

class File(Input):
    """Tails events from a log file on disk.

    Creates events with the field 'data' set to the line received.

    :param string path: path on the file system to the log file(s), wildcards may
      be used to match multiple files.
    :param string statedir: writable directory to store state for files
    """

    def __init__(self, path, statedir=None):
        super(File, self).__init__()
        self.path = path
        self.statedir = statedir
        self.tails = []

    def _run(self):
        paths = glob.glob(self.path)
        while not paths:
            gevent.sleep(0.01)
            paths = glob.glob(self.path)
        q = JoinableQueue()

        self.logger.debug('Tailing %s' % ', '.join(paths))
        self.tails = [Tail(p, q, self.statedir) for p in paths]

        while True:
            data = q.get()
            if data:
                if data.endswith('\n'):
                    data = data[0:-1]
                self.logger.debug('Received: %r' % data)
                self.output.put(Event(data=data))
            q.task_done()

    def stop(self):
        for t in self.tails:
            t.kill()
            t.join()
        super(File, self).stop()
