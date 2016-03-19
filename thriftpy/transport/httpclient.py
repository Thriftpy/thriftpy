# -*- coding: utf-8 -*-

import os
import socket
import sys

from io import BytesIO

from thriftpy._compat import (
    import_urllib,
    import_http_client
)
from thriftpy.transport import TTransportBase


http_client = import_http_client()
urllib = import_urllib()


class THttpClient(TTransportBase):
    """Http implementation of TTransport base.

    Example:
        from thriftpy.transport.httpclient import THttpClient
        from thriftpy.protocol import TCyBinaryProtocolFactory
        from thriftpy.transport import TCyBufferedTransportFactory
        from thriftpy.thrift import TClient

        pp_thrift = thriftpy.load("pingpong.thrift", module_name="pp_thrift")
        uri = 'http://{}:{}{}'.format(host, port, path)
        socket = THttpClient(uri)
        transport = TCyBufferedTransportFactory().get_transport(socket)
        protocol = TCyBinaryProtocolFactory().get_protocol(transport)

        try:
            transport.open()
            client = TClient(pp_thrift.PingService, protocol)
            client.ping()
        finally:
            transport.close()
    """

    def __init__(self, uri):
        """Initialize a HTTP Socket.

        @param host(str)    The http_scheme:://host:port/path to connect to.
        """
        parsed = urllib.parse.urlparse(uri)
        self.scheme = parsed.scheme
        assert self.scheme in ('http', 'https')
        if self.scheme == 'http':
            self.port = parsed.port or http_client.HTTP_PORT
        elif self.scheme == 'https':
            self.port = parsed.port or http_client.HTTPS_PORT
        self.host = parsed.hostname
        self.path = parsed.path
        if parsed.query:
            self.path += '?%s' % parsed.query
        self.__wbuf = BytesIO()
        self.__http = None
        self.__timeout = None
        self.__custom_headers = None

    def open(self):
        if self.scheme == 'http':
            self.__http = http_client.HTTPConnection(self.host, self.port)
        else:
            self.__http = http_client.HTTPSConnection(self.host, self.port)

    def close(self):
        self.__http.close()
        self.__http = None

    def isOpen(self):
        return self.__http is not None

    def setTimeout(self, ms):
        if not hasattr(socket, 'getdefaulttimeout'):
            raise NotImplementedError

        if ms is None:
            self.__timeout = None
        else:
            self.__timeout = ms / 1000.0

    def setCustomHeaders(self, headers):
        self.__custom_headers = headers

    def read(self, sz):
        content = self.response.read(sz)
        return content

    def write(self, buf):
        self.__wbuf.write(buf)

    def __withTimeout(f):
        def _f(*args, **kwargs):
            orig_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(args[0].__timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                socket.setdefaulttimeout(orig_timeout)
                return result
        return _f

    def flush(self):
        if self.isOpen():
            self.close()
        self.open()

        # Pull data out of buffer
        data = self.__wbuf.getvalue()
        self.__wbuf = BytesIO()

        # HTTP request
        self.__http.putrequest('POST', self.path)

        # Write headers
        self.__http.putheader('Host', self.host)
        self.__http.putheader('Content-Type', 'application/x-thrift')
        self.__http.putheader('Content-Length', str(len(data)))

        if (not self.__custom_headers or
                'User-Agent' not in self.__custom_headers):
            user_agent = 'Python/THttpClient'
            script = os.path.basename(sys.argv[0])
            if script:
                user_agent = '%s (%s)' % (
                    user_agent, urllib.parse.quote(script))
                self.__http.putheader('User-Agent', user_agent)

        if self.__custom_headers:
            for key, val in self.__custom_headers.items():
                self.__http.putheader(key, val)

        self.__http.endheaders()

        # Write payload
        self.__http.send(data)

        # Get reply to flush the request
        response = self.__http.getresponse()
        self.code, self.message, self.headers = (
            response.status, response.msg, response.getheaders())
        self.response = response

    # Decorate if we know how to timeout
    if hasattr(socket, 'getdefaulttimeout'):
        flush = __withTimeout(flush)
