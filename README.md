logcabin
========

logcabin is a program for aggregating and processing events from a diverse range
of sources and formats, and outputting to the file system, database or a search
engine.

Quickstart
----------
Install::

    $ pip install logcabin

Configure::

    $ wget https://raw.github.com/artirix/logcabin/master/config/example1.py -O config.py

Run::

    $ logcabin

Send some messages::

    $ echo '{"message": "test log event"}' | nc -u localhost 6000

Contributing
------------
Contributions welcome! Please:

- Fork the project on Github
- Make your feature addition or bug fix, write tests, commit.
- Send me a pull request. Bonus points for topic branches.

Changelog
---------
0.1.0   

- Initial release