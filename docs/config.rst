Configuration
=============

Basics
------

Logcabin uses a python DSL to configure it.

To use a specific configuration pass the ``-c``/``--config`` option with the
filename. It defaults to ``config.py``.

The configuration is a set of stages, which can be any of the input, filter or
output stages. The configuration is interpreted once and the constructed stages
are built into the definition of a pipeline.

With the defined pipeline, logcabin will launch each instance in a greenlet,
each with independent input and output queues, so no single stage blocks
the processing of any other (provided it's not tying up CPU).

Example::

    # import the stages we wish to use
    from flow import Fanin, Fanout
    from inputs.udp import Udp
    from inputs.zeromq import Zeromq
    from filters.json import Json
    from filters.mutate import Mutate
    from outputs.log import Log
    from outputs.elasticsearch import Elasticsearch

    # take input from vanilla udp or a zeromq connection
    with Fanin():
        Udp(port=6000)
        Zeromq(address='tcp://*:2130')

    # transform the plain text input into an structured event with the Json filter, only if field==1.
    with If('field==1'):
        Json()

    # set myfield=abc
    Mutate(set={'myfield': 'abc'})

    # broadcast this to the logcabin log and index to elasticsearch /test/event
    with Fanout():
        Log()
        Elasticsearch(index='test', type='event')

This configures two inputs, which are both processed through the Json filter,
and then output to two outputs in parallel: Log and Elasticsearch.

For full details of the inputs, filters and outputs available see below.

Flows
-----

The pipeline can fanin, and fanout and branch at any point. The following stages
control flow in the pipeline.

Fanin
^^^^^
Fanins create many parallel inputs that will feed onto the same next stage, so
multiple sources can be used for input of events (eg. udp and zeromq).

Sequence
^^^^^^^^
Sequences are a series of stages, in order. The top-level of the configuration
is implicitly a Sequence.

Fanout
^^^^^^
Fanouts create many parallel outputs that run independently.

Branching
^^^^^^^^^
``If`` and ``Switch`` can be used to conditionally call stages.

.. automodule:: logcabin.flow
   :members: Fanin, Sequence, Fanout, If, Switch

Inputs
------

file
^^^^
.. automodule:: logcabin.inputs.file
   :members: File

udp
^^^
.. automodule:: logcabin.inputs.udp
   :members: Udp

zeromq
^^^^^^
.. automodule:: logcabin.inputs.zeromq
   :members: Zeromq

Filters
-------

json
^^^^
.. automodule:: logcabin.filters.json
   :members: Json

syslog
^^^^^^
.. automodule:: logcabin.filters.syslog
   :members: Syslog

mutate
^^^^^^
.. automodule:: logcabin.filters.mutate
   :members: Mutate

regex
^^^^^
.. automodule:: logcabin.filters.regex
   :members: Regex

stats
^^^^^
.. automodule:: logcabin.filters.stats
   :members: Stats

Outputs
-------

elasticsearch
^^^^^^^^^^^^^
.. automodule:: logcabin.outputs.elasticsearch
   :members: Elasticsearch

graphite
^^^^^^^^
.. automodule:: logcabin.outputs.graphite
   :members: Graphite

log
^^^
.. automodule:: logcabin.outputs.log
   :members: Log

mongodb
^^^^^^^
.. automodule:: logcabin.outputs.mongodb
   :members: Mongodb

perf
^^^^
.. automodule:: logcabin.outputs.perf
   :members: Perf

s3
^^
.. automodule:: logcabin.outputs.s3
   :members: S3

zeromq
^^^^^^
.. automodule:: logcabin.outputs.zeromq
   :members: Zeromq
