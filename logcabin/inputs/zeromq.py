from ..event import Event
from .input import Input
import gevent
import zmq.green as zmq

class Zeromq(Input):
    """Receives from a zeromq socket.

    Creates events with the field 'data' set to the packet received.

    :param string address: zeromq address to bind on (default: `tcp://*:2120`)
    :param string mode: connect or bind (default: bind)
    :param string socket: PULL or SUB (default: PULL)
    """
    def __init__(self, address='tcp://*:2120', mode='bind', socket='PULL'):
        if mode not in ('connect', 'bind'):
            raise ValueError('mode should be connect or bind')
        if socket not in ('PULL', 'SUB'):
            raise ValueError('socket should be PULL or SUB')
        super(Zeromq, self).__init__()
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(getattr(zmq, socket))
        self.address = address
        if address == 'tcp://*':
            self.sock.bind_to_random_port(address)
        elif mode == 'connect':
            self.sock.connect(self.address)
        else:
            self.sock.bind(self.address)

    def _run(self):
        try:
            while True:
                data = self.sock.recv()
                self.logger.debug('Received: %r' % data)
                self.output.put(Event(data=data))
                gevent.sleep() # yield for other stages
        finally:
            # cleanup
            self.sock.close()
