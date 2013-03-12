class Context(object):
    def __init__(self):
        self._stack = []

    def push(self, c):
        self._stack.append(c)

    def pop(cls):
        return cls._stack.pop()

    def current(cls):
        return cls._stack[-1]

# Singleton
Context.instance = Context()

class ContextManager(object):
    def __enter__(self):
        Context.instance.push(self)
        return self

    def __exit__(self, *exc_info):
        Context.instance.pop()

    def add(self, stage):
        """Override add to handle child adds"""
        pass

class DummyContext(ContextManager):
    def __init__(self):
        self.stages = []

    def add(self, stage):
        self.stages.append(stage)
