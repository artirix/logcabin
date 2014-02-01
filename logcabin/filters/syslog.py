import re
import dateutil.parser

from .filter import Filter

class Syslog(Filter):
    """Parse a syslog encoded field.

    This sets the fields:
    
    - timestamp
    - facility
    - severity
    - host
    - program
    - pid
    - message

    :param string field: the field containing the syslog message (default: data)
    :param boolean consume: whether to remove the field after decoding (default: true)

    Example::

        Syslog()
    """

    def __init__(self, field='data', consume=True, on_error='reject'):
        super(Syslog, self).__init__(on_error=on_error)
        self.field = field
        self.consume = consume

    re_syslog = re.compile(r'<(?P<prio>\d+)>(?P<timestamp>.+?) '
        r'(?P<host>\S*) (?P<program>\S+?)'
        r'(\[(?P<pid>\d+)\])?: (?P<message>.+)')
    facilities = ["kernel", "user-level", "mail", "system", "security/authorization",
        "syslogd", "line printer", "network news", "UUCP", "clock", "security/authorization",
        "FTP", "NTP", "log audit", "log alert", "clock", "local0", "local1", "local2",
        "local3", "local4", "local5", "local6", "local7"]
    severities = ["Emergency", "Alert", "Critical", "Error", "Warning", "Notice",
        "Informational", "Debug"]
    months = dict((v, k) for k, v in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']))

    def process(self, event):
        if self.field in event:
            data = event[self.field]

            try:
                fields = self._decode(data)
                self.logger.debug('syslog decoded: %s' % fields)
                event.update(fields)
                if self.consume:
                    del event[self.field]

                return True
            except ValueError as ex:
                self._error(event, ex)
                return False

    def _decode(self, data):
            m = self.re_syslog.match(data)
            if m:
                d = m.groupdict()
                prio = int(d.pop('prio'))
                try:
                    d['facility'] = self.facilities[prio >> 3]
                except IndexError:
                    d['facility'] = 'unknown'
                d['severity'] = self.severities[prio & 7]

                timestamp = d.pop('timestamp')
                d['timestamp'] = dateutil.parser.parse(timestamp)
                return d
            else:
                raise ValueError('invalid syslog')
