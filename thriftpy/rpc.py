# -*- coding: utf-8 -*-

import contextlib

from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.thrift import TProcessor, TClient
from thriftpy.transport import TSocket, TBufferedTransport, TServerSocket
from thriftpy.server import TThreadedServer


def make_client(service, host, port, proto_factory=TBinaryProtocolFactory()):
    transport = TBufferedTransport(TSocket(host, port))
    protocol = proto_factory.get_protocol(transport)
    transport.open()
    return TClient(service, protocol)


def make_server(service, handler, host, port,
                proto_factory=TBinaryProtocolFactory()):
    processor = TProcessor(service, handler)
    transport = TServerSocket(host=host, port=port)
    server = TThreadedServer(processor, transport,
                             iprot_factory=proto_factory)
    return server


@contextlib.contextmanager
def client_context(service, host, port,
                   proto_factory=TBinaryProtocolFactory()):
    try:
        transport = TBufferedTransport(TSocket(host, port))
        protocol = proto_factory.get_protocol(transport)
        transport.open()
        yield TClient(service, protocol)
    finally:
        transport.close()
