import logging


class BasicRequest(object):

    protocol = 'http'
    host = 'www.centaurstech.com'
    port = 80
    endpoint = '/'

    def __init__(self):
        self.logger = logging.getLogger("RotatingLog")

    def to_uri(self, endpoint=None):
        endpoint = endpoint or self.endpoint
        return '{0}://{1}:{2}{3}'.format(self.protocol, self.host, self.port, endpoint)
