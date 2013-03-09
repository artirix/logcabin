# import everything we're using
from flow import Fanin, Switch
from inputs.udp import Udp
from inputs.zeromq import Zeromq
from filters.json import Json
from filters.stats import Stats
from outputs.graphite import Graphite
from outputs.elasticsearch import Elasticsearch
from outputs.file import File
from outputs.s3 import S3

# input from a couple of sources
with Fanin():
    Udp(port=6000)
    Zeromq()

# parse json
Json()
# generate statistic counts (suitable for graphite)
Stats(timings={'rails.{controller}.{action}.duration': 'duration'})
# write the data to a rotating log file
File(filename='mylogs.log', max_size=1000000, compress='gz')
# decide the destination because on some tags
with Switch() as case:
    # on log roll, archive the file to S3
    with case("'fileroll' in tags"):
        S3(access_key='xyz',
           secret_key='123',
           bucket='mybucket',
           path='logs/{timestamp:%Y%m%dT%H%M}')
    # write the aggregate statistics to graphite
    with case("'stat' in tags"):
        Graphite()
    # otherwise just index into elasticsearch
    with case.default:
        Elasticsearch(index='logcabin', type='event')
