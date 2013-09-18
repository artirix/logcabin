from common import ProcessingStage, MultiStage
from util import BroadcastQueue
import inspect

class Fanin(MultiStage):
    """
    This merges all of the outputs of the child stages to a single queue.

    Syntax::

        with Fanin():
            Udp()
            Zeromq()
    """

    def setup(self, q):
        self.output = q
        for s in self.stages:
            s.setup(self.output)
        return None # fanin has no inputs

class Sequence(MultiStage):
    """
    This connects the output of the preceding stage to the input of the next,
    and so on, so the event is processed by each stage one after the other, in
    order.

    Syntax::

        with Sequence():
            Mutate()
            Mutate()
            ...
    """

    def setup(self, q):
        self.output = q
        # this is setup backwards, so the output from the current is
        # connected to the input of the successor, and the input of the current
        # will be connected to the output of the predecessor.
        for s in reversed(self.stages):
            q = s.setup(q)
        self.input = q
        return self.input

class Fanout(MultiStage):
    """
    This enqueues the event onto multiple input queues in parallel.

    Syntax::

        with Fanout():
            Log()
            Elasticsearch()
            Mongodb()
            ...
    """

    def setup(self, q):
        self.output = q
        queues = []
        for s in self.stages:
            queues.append(s.setup(q))
        self.input = BroadcastQueue(queues)
        return self.input

from contextlib import contextmanager

class DefaultDictProxy(object):
    """Proxies attribute request to dict, missing keys default to None"""
    def __init__(self, d):
        self.d = d

    def __getattr__(self, k):
        # properties on event (eg .tags) take preference over elements
        return self[k]

    def __getitem__(self, k):
        if hasattr(self.d, k):
            return getattr(self.d, k)
        else:
            return self.d.get(k)

class Switch(ProcessingStage, MultiStage):
    """Branch flow based on a condition.

    The cases are specified using this syntax. The condition may be a lambda
    expression or code string::

        with Switch() as case:
            with case(lambda ev: ev.field == 'value'):
                Json()
            with case('field2 == "value2"'):
                Mutate()
            with case.default:
                Regex(regex='abc')
    """

    def __init__(self, on_error='reject'):
        super(Switch, self).__init__(on_error=on_error)
        self.cases = []

    @contextmanager
    def __call__(self, condition):
        if isinstance(condition, str):
            # python code as string
            code = compile(condition, 'string', 'eval')
            condition = lambda ev: eval(code, {}, ev)

        br = Sequence()
        self.cases.append((condition, br))
        with br:
            yield

    @property
    def default(self):
        return self(lambda x: True)

    def setup(self, q):
        # separate queue for the incoming condition,
        # and fan in on the individual pipelines.
        for t, br in self.cases:
            br.setup(q)
        return super(Switch, self).setup(q)

    def start(self):
        # call both multistage to start the branch and ProcessingStage greenlet
        ProcessingStage.start(self)
        MultiStage.start(self)

    def stop(self):
        # stop the branch and our greenlet
        ProcessingStage.stop(self)
        MultiStage.stop(self)

    def process(self, event):
        # pass the event into the sub-queue for the applicable pipeline
        ret = True
        for case, br in self.cases:
            if case(DefaultDictProxy(event)):
                br.input.put(event)
                ret = False
                break

        # if no condition handles it, pass straight on (True)
        return ret

class If(ProcessingStage, MultiStage):
    """
    Conditionally execute stages.

    The syntax is as follows. The condition may be a lambda expression or code
    string::

        with If('field==1'):
            Json()
    """

    def __init__(self, condition, on_error='reject'):
        super(If, self).__init__(on_error=on_error)
        if isinstance(condition, str):
            # python code as string
            self.condition_text = condition
            code = compile(condition, 'string', 'eval')
            condition = lambda ev: eval(code, {}, ev)
        else:
            self.condition_text = inspect.getsource(condition)
        self.condition = condition

    # configuration contexts
    def __enter__(self):
        super(If, self).__enter__()
        self.branch = Sequence()
        return self.branch.__enter__()

    def __exit__(self, *exc_info):
        self.branch.__exit__()
        return super(If, self).__exit__()

    def setup(self, q):
        # pass output queue to the branch
        self.branch.setup(q)
        return super(If, self).setup(q)

    def start(self):
        # call both multistage to start the branch and ProcessingStage greenlet
        ProcessingStage.start(self)
        MultiStage.start(self)

    def stop(self):
        # stop the branch and our greenlet
        ProcessingStage.stop(self)
        MultiStage.stop(self)

    def process(self, event):
        # pass the event into the sub-queue for the applicable pipeline
        result = self.condition(DefaultDictProxy(event))
        self.logger.debug("Condition: %s evaluated to %s" % (self.condition_text, result))
        if result:
            self.branch.input.put(event)
            # sub-pipeline will dequeue
            return False
        else:
            # if condition False, pass straight on (True)
            return True
