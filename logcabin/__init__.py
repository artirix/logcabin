#!/usr/bin/env python

import sys

__version__ = (1, 0, 7, "final", 0)

def main():
    # avoid importing all dependencies when doing 'import logcabin' for
    # __version__
    from __main__ import LogCabin
    app = LogCabin()
    success = app.run()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
