# -*- coding: utf-8 -*-

from __future__ import absolute_import

import contextlib

from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.server import TThreadedServer
from thriftpy.thrift import TProcessor, TClient
from thriftpy.transport import (
    TBufferedTransportFactory,
    TServerSocket,
    TSocket,
)


def make_client(service, host, port,
                proto_factory=TBinaryProtocolFactory(),
                transport_factory=TBufferedTransportFactory(),
                timeout=None):
    socket = TSocket(host, port)
    if timeout:
        socket.set_timeout(timeout)
    transport = transport_factory.get_transport(socket)
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
                   proto_factory=TBinaryProtocolFactory(),
                   transport_factory=TBufferedTransportFactory(),
                   timeout=None):
    try:
        socket = TSocket(host, port)
        if timeout:
            socket.set_timeout(timeout)
        transport = transport_factory.get_transport(socket)
        protocol = proto_factory.get_protocol(transport)
        transport.open()
        yield TClient(service, protocol)
    finally:
        transport.close()
