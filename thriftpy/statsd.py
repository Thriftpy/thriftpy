# -*- coding: utf-8 -*-

import sys
import socket
import logging
import urlparse

logger = logging.getLogger(__name__)


class Client(object):
    """Statsd client.

    Origin: https://github.com/sivy/pystatsd/blob/master/pystatsd/statsd.py
    """

    def __init__(self, statsd_dsn=None):
        self.statsd_dsn = statsd_dsn
        self.addr = None
        self.udp_sock = None
        self.is_in_zeus_core = 'zeus_core' in sys.modules

    def _init_sock(self):
        """Lazy init udp sock with addr setting."""
        if self.statsd_dsn is None:
            from zeus_core.ves.config import load_core_config
            self.statsd_dsn = load_core_config().statsd_uri
        self.uri = urlparse.urlparse(self.statsd_dsn)
        self.addr = (socket.gethostbyname(self.uri.hostname), self.uri.port)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _fullname(self, name, server=None, client=None):
        from zeus_core.tracker import get_client_app_id
        from zeus_core.ves.config import load_app_config
        if server:
            return "{0}.{1}".format(name, get_client_app_id())
        return "{0}.{1}".format(name, load_app_config().app_id)

    def increment(self, name, server=False, client=False, sample_rate=1):
        """
        Increments one or more stats counters
        >>> statsd_client.increment('some.int')
        >>> statsd_client.increment('some.int',0.5)
        """
        if not self.is_in_zeus_core:
            return
        if not isinstance(name, list):
            names = [name]

        data = dict((name, "%s|c" % 1) for name in names)
        sampled_data = ["%s:%s" % (self._fullname(stat, server=server, client=client), value)
                        for stat, value in data.iteritems()]
        self.send('\n'.join(sampled_data), sample_rate)

    # alias
    incr = increment

    def send(self, data, sample_rate=1):
        """
        Squirt the metrics over UDP
        """
        if self.udp_sock is None:
            self._init_sock()

        if data is None:
            return

        if not all(self.addr):
            logger.error('Statsd uri is invalid.')
            return

        try:
            self.udp_sock.sendto(data, self.addr)
        except:
            logger.exception("unexpected error")

statsd_client = Client()
