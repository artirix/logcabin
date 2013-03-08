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
    :param string index: (required) elasticsearch index
    :param string type: (required) elasticsearch type
    """

    RETRIES = 10

    def __init__(self, index, type, host='localhost', port=9200):
        super(Elasticsearch, self).__init__()
        self.host = host
        self.port = port
        self.index = index
        self.type = type
        self.url = 'http://%s:%s/%s/%s/' % (self.host, self.port, self.index, self.type)

    def process(self, event):
        data = event.to_json()

        success = False
        delay = 1.0
        for retry in xrange(self.RETRIES):
            try:
                res = urllib2.urlopen(self.url, data=data)
                result = json.load(res)
                success = result['ok']
                if not success:
                    self.logger.error('Indexing failed: %s' % result)
                break
            except urllib2.URLError as ex:
                delay *= 2.0
                self.logger.warn('Unable to index: %s, retrying in %ds' % (ex, delay))
                gevent.sleep(delay)

        if success:
            self.logger.debug('Indexed to elasticsearch: index:%s type:%s id:%s' % (self.index, self.type, result['_id']))
