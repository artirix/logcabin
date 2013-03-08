from ..event import Event
from .input import Input
import zmq.green as zmq

class Zeromq(Input):
    """Receives from a zeromq socket.

    :param string address: zeromq address to bind on (default: `tcp://*:2120`)
    """
    def __init__(self, address='tcp://*:2120'):
        super(Zeromq, self).__init__()
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(zmq.PULL)
        self.address = address
        self.sock.bind(self.address)

    def _run(self):
        try:
            while True:
                data = self.sock.recv()
                self.logger.debug('Received: %r' % data)
                self.output.put(Event(data=data))
        finally:
            # cleanup
            self.sock.close()
