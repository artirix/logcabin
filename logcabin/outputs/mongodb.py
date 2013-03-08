from .output import Output
import pymongo

class Mongodb(Output):
    """Outputs to a mongodb collection.

    :param string host: mongodb host
    :param integer port: mongodb port
    :param string database: mongodb database
    :param string collection: mongodb collection
    """

    def __init__(self, host='localhost', port=27017, database='test', collection='events'):
        super(Mongodb, self).__init__()
        self.host = host
        self.port = port
        self.database = database
        self.collection = collection
        self.conn = pymongo.MongoClient(self.host)

    def process(self, event):
        d = dict(event)
        self.conn[self.database][self.collection].insert(d)
