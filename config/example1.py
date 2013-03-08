from flow import Fanin, Switch
from inputs.udp import Udp
from inputs.zeromq import Zeromq
from filters.json import Json
from filters.stats import Stats
from outputs.log import Log
from outputs.elasticsearch import Elasticsearch
from outputs.file import File
from outputs.s3 import S3

with Fanin():
    Udp(port=6000)
    Zeromq()

Json()
Stats(timings={'rails.{controller}.{action}.duration': 'duration'})
File(filename='mylogs.log', max_size=10, compress='gz')
with Switch() as case:
    with case("'fileroll' in tags"):
        S3(access_key='xyz',
           secret_key='123',
           bucket='mybucket',
           path='logs/{timestamp:%Y%m%dT%H%M}')
    with case("'stat' in tags"):
        Log()
    with case.default:
        Elasticsearch(index='logcabin', type='event')
