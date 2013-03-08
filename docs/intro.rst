Introduction
============

logcabin is a program for aggregating and processing events from a diverse range
of sources and formats, and outputting to the file system, database or a search
engine.

Features
--------

- Simple, but flexible configuration DSL in python.

- High concurrency: using gevent coroutines all I/O processing is parallelized.

- Wide variety of input formats: syslog, udp, zeromq.

- Wide variety of output formats: file, mongodb, elasticsearch, graphite.

- Decent performance: on a t1.micro, the smallest Amazon EC2 instance size,
  logcabin can burst 10,000 req/s and sustain 1,000 req/s.

- Fast startup (< 1s).

- Lightweight on memory (typically ~20MB resident).

- Easy to add / extend with python code.

Alternatives
------------

Logging frameworks is a fairly crowded space, and indeed logcabin was inspired
by, and owes a debt of gratitude to logstash, and its brilliant ideas.

So why create another logging framework?

- some frameworks only support simple topologies with a single data flow through
  the pipeline. This doesn't allow for sophistication when receiving data from a
  diverse range of sources.

- easy on the resources - logstash is built on jruby and jvm consumes >200MB
  resident. This is a decent chunk of memory to run locally as a lightweight log
  forwarder or for cheap t1.micro instances.

- fast startup is crucial for testing configurations iteratively.

- gevent + zmq = cool toys to play with :-)
