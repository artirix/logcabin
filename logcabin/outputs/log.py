from .output import Output

class Log(Output):
    """Logging output.

    :param string message: message to log (optional)

    Example::

        Log(message="event:")
    """
    def __init__(self, message=''):
        super(Log, self).__init__()
        self.message = message
        if message:
            self.message += ' '

    def process(self, event):
        self.logger.info('%s%r' % (self.message, event))
