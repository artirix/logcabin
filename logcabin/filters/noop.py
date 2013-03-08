from .filter import Filter

class Noop(Filter):
    """Test filter that does nothing"""
    
    def process(self, event):
        pass
