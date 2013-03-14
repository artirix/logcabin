import gevent
import gevent.socket

from ..event import Event
from .input import Input

class Udp(Input):
    """Receives from a udp port.

    Creates events with the field 'data' set to the packet received.

    :param integer port: listening port
    """

    def __init__(self, port):
        super(Udp, self).__init__()
        self.port = port
        self.sock = gevent.socket.socket(gevent.socket.AF_INET, gevent.socket.SOCK_DGRAM)
        self.sock.setsockopt(gevent.socket.SOL_SOCKET, gevent.socket.SO_BROADCAST, 1)
        self.sock.bind(('', self.port))

    def _run(self):
        while True:
            data = self.sock.recv(4096)
            self.logger.debug('Received: %r' % data)
            self.output.put(Event(data=data))
            gevent.sleep() # yield for other stages
