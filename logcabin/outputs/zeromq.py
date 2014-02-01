from .output import Output
import zmq.green as zmq

class Zeromq(Output):
    """Outputs on a zeromq socket.

    :param string address: zeromq address (default: `tcp://*:2120`)
    :param string mode: connect or bind (default: connect)
    :param string socket: PUSH or PUB (default: PUSH)

    Example::

        Zeromq(address="tcp://relay:2120", mode="connect", socket="PUSH")
    """
    def __init__(self, address='tcp://127.0.0.1:2120', mode='connect', socket='PUSH'):
        if mode not in ('connect', 'bind'):
            raise ValueError('mode should be connect or bind')
        if socket not in ('PUSH', 'PUB'):
            raise ValueError('socket should be PUSH or PUB')

        super(Zeromq, self).__init__()
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(getattr(zmq, socket))
        self.address = address
        if mode == 'connect':
            self.sock.connect(self.address)
        else:
            self.sock.bind(self.address)

    def process(self, event):
        data = event.to_json()
        self.sock.send(data)
