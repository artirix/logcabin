import gevent
import gevent.socket

from ..event import Event
from .input import Input

class Udp(Input):
    """Receives from a udp port.

    Creates events with the field 'data' set to the packet received.

    :param integer port: listening port

    Example::

        Udp(port=6000)
    """

    def __init__(self, port, allow_hosts=[]):
        super(Udp, self).__init__()
        self.port = port
        self.sock = gevent.socket.socket(gevent.socket.AF_INET, gevent.socket.SOCK_DGRAM)
        self.sock.setsockopt(gevent.socket.SOL_SOCKET, gevent.socket.SO_BROADCAST, 1)
        self.sock.bind(('', self.port))

    def _run(self):
        while True:
            data, address = self.sock.recvfrom(4096)
            if len(self.allow_hosts) > 0:
                if not address[0] in self.allow_hosts:
                    #fail2ban: failregex = reject host \[<HOST>\]
                    self.logger.error("reject host [%s]" % address[0])
                    #TODO: close sock ?
                    continue
            self.logger.debug('Received: %r' % data)
            self.output.put(Event(data=data))
            gevent.sleep() # yield for other stages
