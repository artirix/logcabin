from .output import Output
import boto
import boto.s3.key

class S3(Output):
    """Uploads to an S3 bucket.

    This should follow the File output, in order to upload the rolled log files
    to S3::

        File(filename='log/batch.log', )
        If(lambda ev: 'fileroll' in ev.tags):
            S3(access_key='...', secret_key='...',
               bucket='x', path='logs/{timestamp:%Y-%m-%d/%H%M%S}.log')

    Bucket or path may by formatted by event, eg. to upload to a timestamped path:
    path='{timestamp:%Y-%m-%d/%H%M%S}.log'

    :param string access_key: Amazon S3 access key
    :param string secret_key: Amazon S3 secret key
    :param string bucket: the bucket name
    :param string path: the path
    """

    def __init__(self, access_key, secret_key, bucket, path):
        super(S3, self).__init__()
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.path = path

    def process(self, event):
        bucket = event.format(self.bucket)
        path = event.format(self.path)

        filename = event['filename']
        self.logger.info('Uploading %s to s3://%s/%s' % (filename, bucket, path))
        s3 = boto.connect_s3(self.access_key, self.secret_key)
        bucket = s3.get_bucket(bucket)
        k = bucket.new_key(path)
        k.set_contents_from_filename(filename)
