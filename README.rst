logcabin
========

.. image:: https://travis-ci.org/artirix/logcabin.png?branch=master
        :target: https://travis-ci.org/artirix/logcabin

logcabin is a program for aggregating and processing events from a diverse range
of sources and formats, and outputting to the file system, database or a search
engine.

Quickstart
----------
Install::

    $ pip install logcabin

Configure::

    $ wget https://raw.github.com/artirix/logcabin/master/config/simple.py -O config.py

Run::

    $ logcabin

Send some messages::

    $ echo '{"message": "test log event"}' | nc -u localhost 6000
    $ cat output.log

Dependencies
------------
pip will install gevent, which needs libevent-dev (or equivalent package) to
build::

    $ apt-get install libevent-dev

All other dependencies are optional, and only required if you use that module.

zeromq
^^^^^^
Install::

    $ apt-get install libzmq1-dev (or equivalent)
    $ pip install -U pyzmq
    (>= 2.2.0.1)

mongodb
^^^^^^^
Install::

    $ pip install pymongo

Docs
----
See: http://logcabin.readthedocs.org/en/latest/

Contributing
------------
Contributions welcome! Please:

- Fork the project on Github
- Make your feature addition or bug fix, write tests, commit.
- Send me a pull request. Bonus points for topic branches.

Changelog
---------
1.0.7

- Add some debugging logging

1.0.6

- Switch to milliseconds - more ISO8601 standard

1.0.5

- Save precious bytes on json output

1.0.4

- Improve error messages on unparseable Json

- Add some debug logging to Graphite

1.0.3

- add copy action in Mutate object

1.0.2

- Fix bug in when setting File statedir

1.0.1

- Add resume to input File tailing

1.0

- Add timestamp rolling to Output File

- Add url unescape filter

- Add event setter and tidy docs

0.1b12

- graphite output should reconnect on socket errors

0.1b11

- Stats filter: zero=True/False option to generate zero data points

0.1b10

- Add Python stage for custom python code

0.1b9

- Yield in input stages for better behaviour

- Improve exception catching

0.1b8

- Robustness and general bug fixes

0.1b7

- Add support to stats for wildcarding and nested fields

0.1b6

- Add index/type formatting for elasticsearch

0.1b5

- Bug fix for flow stopping at If/Switch
- Add rename and unset to Mutate

0.1b4

- Documentation improvements

0.1b3

- Add file input and zeromq output.

0.1b2

- Initial release