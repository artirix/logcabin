# import everything we're using
from flow import Fanout
from inputs.zeromq import Zeromq
from outputs.file import File
from outputs.elasticsearch import Elasticsearch
from outputs.mongodb import Mongodb

# single zeromq input
Zeromq()

# Broadcast the event in parallel to all of the following outputs. The event
# will simultaneously be written to mylogs.log, indexed to elasticsearch and
# saved to mongodb.
with Fanout():
    File(filename='mylogs.log', max_size=10, compress='gz')
    Elasticsearch(index='events', type='{program}')
    Mongodb()
