import tempfile
import shutil
import os

def assertEventEquals(self, expected, actual):
    """Compares two events for equality, ignoring the timestamps."""
    expected = dict(expected)
    del expected['timestamp']
    actual = dict(actual)
    del actual['timestamp']
    self.assertEquals(expected, actual)

class Matcher(object):
    """Helper for test assertions"""
    def __init__(self, compare):
        self.compare = compare
        
    def __eq__(self, other):
        return self.compare(other)
    
    def __repr__(self):
        return repr(self.compare)
        
def any(_):
    """Matches anything"""
    return True

def about(x, p=0):
    fmt = '%%.%df' % p
    return Matcher(lambda t: fmt % x == fmt % t)

def between(x, y):
    return Matcher(lambda t: t > x and t < y)
    
ANY = Matcher(any)

class TempDirectory(object):
    """Temporary directory with context manager support. Inspired by python 3."""

    def __init__(self, suffix='', prefix='tmp', dir=None, change=True):
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
        self.change = change

    def __enter__(self):
        self.name = tempfile.mkdtemp(self.suffix, self.prefix, self.dir)
        if self.change:
            self.oldpwd = os.getcwd()
            os.chdir(self.name)
        return self

    def __exit__(self, *excinfo):
        if self.change:
            os.chdir(self.oldpwd)
        shutil.rmtree(self.name)
