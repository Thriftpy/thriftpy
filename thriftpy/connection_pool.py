# -*- coding: utf-8 -*-

import logging
import datetime
import contextlib

logger = logging.getLogger(__name__)


class ThriftBaseClient(object):

    def __init__(self, transport, protocol, client, keepalive=None):
        self.transport = transport
        self.protocol = protocol
        self.client = client
        self.alive_until = datetime.datetime.now() + \
            datetime.timedelta(seconds=keepalive) if keepalive else None

    def __repr__(self):
        return "<%s service=%s>" % (
            self.__class__.__name__,
            self.client.__class__.__module__
            )

    def __getattr__(self, name):
        return getattr(self.client, name)

    def close(self):
        try:
            self.transport.close()
        except Exception as e:
            logger.warn("Connction close failed: %r" % e)

    def is_expired(self):
        return self.alive_until and datetime.datetime.now() > self.alive_until

    def test_connection(self):
        if self.is_expired():
            return False
        try:
            self.ping()
            return True
        except:
            return False

    @classmethod
    def connect(cls, service, host, port, timeout=30):
        raise NotImplementedError

    @property
    def TTransportException(self):
        raise NotImplementedError


class ThriftClient(ThriftBaseClient):
    @property
    def TTransportException(self):
        from thrift.transport.TTransport import TTransportException
        return TTransportException

    @classmethod
    def connect(cls, service, host, port, timeout=30, keepalive=None):
        from thrift.transport import TSocket
        from thrift.transport import TTransport
        from thrift.protocol import TBinaryProtocol

        transport = TSocket.TSocket(host, port)
        transport.setTimeout(timeout * 1000)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocolAccelerated(transport)

        transport.open()

        return cls(
            transport=transport,
            protocol=protocol,
            client=service.Client(protocol),
            keepalive=keepalive
            )


class ThriftPyClient(ThriftBaseClient):
    @property
    def TTransportException(self):
        from thriftpy.transport import TTransportException
        return TTransportException

    @classmethod
    def connect(cls, service, host, port, timeout=30, keepalive=None):
        from thriftpy.thrift import TClient
        from thriftpy.transport import TSocket
        from thriftpy.protocol import TBinaryProtocolFactory
        from thriftpy.transport import TBufferedTransportFactory

        PROTO_FACTORY = TBinaryProtocolFactory

        TRANS_FACTORY = TBufferedTransportFactory

        transport = TRANS_FACTORY().get_transport(TSocket(host, port))
        protocol = PROTO_FACTORY().get_protocol(transport)
        transport.open()

        return cls(
            transport=transport,
            protocol=protocol,
            client=TClient(service, protocol),
            keepalive=keepalive
            )


class ThriftPyCyClient(ThriftBaseClient):
    @property
    def TTransportException(self):
        from thriftpy.transport import TTransportException
        return TTransportException

    @classmethod
    def connect(cls, service, host, port, timeout=30, keepalive=None):
        from thriftpy.thrift import TClient
        from thriftpy.transport import TSocket
        from thriftpy.protocol import TCyBinaryProtocolFactory
        from thriftpy.transport import TCyBufferedTransportFactory

        PROTO_FACTORY = TCyBinaryProtocolFactory
        TRANS_FACTORY = TCyBufferedTransportFactory
        transport = TRANS_FACTORY().get_transport(TSocket(host, port))
        protocol = PROTO_FACTORY().get_protocol(transport)
        transport.open()

        return cls(
            transport=transport,
            protocol=protocol,
            client=TClient(service, protocol),
            keepalive=keepalive
            )


class ClientPool(object):
    def __init__(self, service, host, port, timeout=30, name=None,
                 raise_empty=False, max_conn=30, connction_class=ThriftClient,
                 keepalive=None):
        self.service = service
        self.host = host
        self.port = port
        self.timeout = timeout
        self.name = name or service.__name__
        self.connections = set()
        self.raise_empty = raise_empty
        self.max_conn = max_conn
        self.connction_class = connction_class
        self.keepalive = keepalive

    def keys(self):
        return set([self.name, self.service.__name__])

    def __repr__(self):
        return "<%s service=%r>" % (
            self.__class__.__name__,
            self.keys()
            )

    def get_client_from_pool(self):
        if not self.connections:
            if self.raise_empty:
                raise self.Empty
            return

        connection = self.connections.pop()
        if connection.test_connection():  # make sure old connection is usable
            return connection
        else:
            connection.close()

    def put_back_connection(self, conn):
        assert isinstance(conn, ThriftBaseClient)
        if self.max_conn > 0 and len(self.connections) < self.max_conn:
            self.connections.add(conn)
        else:
            conn.close()

    def produce_client(self):
        return self.connction_class.connect(
            self.service,
            self.host,
            self.port,
            self.timeout,
            keepalive=self.keepalive
            )

    def get_client(self):
        return self.get_client_from_pool() or self.produce_client()

    def __getattr__(self, name):
        client = self.get_client()
        api = getattr(client, name, None)
        if name not in client.__dict__ and callable(api):
            def call(*args, **kwds):
                ret = api(*args, **kwds)
                self.put_back_connection(client)
                return ret
            return call
        self.put_back_connection(client)
        raise AttributeError("%s not found in %s" % (name, client))

    @contextlib.contextmanager
    def connection_ctx(self):
        client = self.get_client()
        try:
            yield client
            self.put_back_connection(client)
        except client.TTransportException:
            client.close()
            raise
        except Exception:
            self.put_back_connection(client)
            raise
