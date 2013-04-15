from .filter import Filter

class Python(Filter):
    """Call out to a python function for adding custom functionality.

    :param callable function: callable taking the event as an argument
    """

    def __init__(self, function, on_error='reject'):
        super(Python, self).__init__(on_error=on_error)
        self.function = function

    def process(self, event):
        return self.function(event)
