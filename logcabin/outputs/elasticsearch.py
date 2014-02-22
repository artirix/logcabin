from .output import Output
import gevent
import gevent.monkey
gevent.monkey.patch_socket()
import urllib2
import json

class Elasticsearch(Output):
    """Outputs to an elasticsearch index.

    :param string host: elasticsearch host
    :param integer port: elasticsearch port
    :param string index: (required) elasticsearch index. This can be formatted by fields in the event.
    :param string type: (required) elasticsearch type. This can be formatted by fields in the event.

    Example configuration for kibana::

        Mutate(rename={'@timestamp': 'timestamp', '@message': 'message'})
        Elasticsearch(index='logstash-{@timestamp:%Y.%m.%d}', type='event')
    """

    RETRIES = 10

    def __init__(self, index, type, host='localhost', port=9200):
        super(Elasticsearch, self).__init__()
        self.host = host
        self.port = port
        self.index = index
        self.type = type

    def process(self, event):
        data = event.to_json()
        index = event.format(self.index)
        itype = event.format(self.type)
        if not index:
            raise ValueError("index is empty")
        if not itype:
            raise ValueError("type is empty")

        url = 'http://%s:%s/%s/%s/' % (self.host, self.port, index, itype)

        success = False
        delay = 1.0
        for retry in xrange(self.RETRIES):
            try:
                res = urllib2.urlopen(url, data=data)
                # 200 response indicates all is well
                success = True
                result = json.load(res)
                break
            except urllib2.HTTPError as ex:
                if ex.getcode() == 400:
                    # Bad Request - do not retry
                    self.logger.error("Bad request: %s, not retrying" % (ex,))
                    break
                else:
                    delay *= 2.0
                    self.logger.warn('Unable to index: %s, retrying in %ds' % (ex, delay))
                    gevent.sleep(delay)
            except urllib2.URLError as ex:
                delay *= 2.0
                self.logger.warn('Unable to index: %s, retrying in %ds' % (ex, delay))
                gevent.sleep(delay)

        if success:
            self.logger.debug('Indexed to elasticsearch: index:%s type:%s id:%s' % (index, itype, result['_id']))
