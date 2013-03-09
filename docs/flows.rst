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

