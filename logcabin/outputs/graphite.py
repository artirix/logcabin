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
        self.connect()
        
    def connect(self):
        self.sock = socket.socket()
        self.sock.connect((self.host, self.port))
        self._metrics = []
        
    def process(self, event):
        metric = event.metric
        timestamp = int(time.mktime(event.timestamp.timetuple()))
        data = []
        for s, value in event.stats.iteritems():
            path = '%s.%s' % (metric, s)
            d = (path, (timestamp, value))
            data.append(d)

        # wire protocol is a 4-byte length, followed by pickled representation,
        # see: http://graphite.readthedocs.org/en/1.0/feeding-carbon.html
        payload = pickle.dumps(data)
        header = struct.pack("!L", len(payload))
        message = header + payload
        self.sock.sendall(message)
