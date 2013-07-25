import gevent
import gevent.socket as socket
import pickle
import struct
import time

from .output import Output

class Graphite(Output):
    """Upload stats data to a graphite server.

    :param string host: graphite server hostname
    :param string port: graphite server port
    """

    def __init__(self, host='localhost', port=2004):
        super(Graphite, self).__init__()
        self.host = host
        self.port = port
        self._metrics = []
        self._connected = False
        
    def flush(self):
        if not self._connected:
            self.connect()

        # wire protocol is a 4-byte length, followed by pickled representation,
        # see: http://graphite.readthedocs.org/en/1.0/feeding-carbon.html
        payload = pickle.dumps(self._metrics)
        header = struct.pack("!L", len(payload))
        message = header + payload
        self.logger.debug("Flushing %d metrics to graphite %s:%d" % (len(self._metrics), self.host, self.port))
        try:
            self.sock.sendall(message)
        except socket.error:
            self.sock.close()
            self.connect()
            self.sock.sendall(message)
        self._metrics = []

    def connect(self):
        while True:
            try:
                self.sock = socket.socket()
                self.sock.connect((self.host, self.port))
                break
            except socket.error:
                self.logger.warn("Couldn't connect to graphite: %s:%s, retrying in 1s" % (self.host, self.port))
                gevent.sleep(1.0)

        self._connected = True
        
    def process(self, event):
        metric = event.metric
        timestamp = int(time.mktime(event.timestamp.timetuple()))
        for s, value in event.stats.iteritems():
            path = '%s.%s' % (metric, s)
            d = (path, (timestamp, value))
            self._metrics.append(d)

        self.flush()
