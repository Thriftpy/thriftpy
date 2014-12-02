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


def make_client(service, host="localhost", port=9090, unix_socket=None,
                proto_factory=TBinaryProtocolFactory(),
                trans_factory=TBufferedTransportFactory(),
                timeout=None):
    if unix_socket:
        socket = TSocket(unix_socket=unix_socket)
    elif host and port:
        socket = TSocket(host, port)
    else:
        raise ValueError("Either host/port or unix_socket must be provided.")

    if timeout:
        socket.set_timeout(timeout)

    transport = trans_factory.get_transport(socket)
    protocol = proto_factory.get_protocol(transport)
    transport.open()
    return TClient(service, protocol)


def make_server(service, handler,
                host="localhost", port=9090, unix_socket=None,
                proto_factory=TBinaryProtocolFactory(),
                trans_factory=TBufferedTransportFactory()):
    processor = TProcessor(service, handler)
    if unix_socket:
        server_socket = TServerSocket(unix_socket=unix_socket)
    elif host and port:
        server_socket = TServerSocket(host=host, port=port)
    else:
        raise ValueError("Either host/port or unix_socket must be provided.")

    server = TThreadedServer(processor, server_socket,
                             iprot_factory=proto_factory,
                             itrans_factory=trans_factory)
    return server


@contextlib.contextmanager
def client_context(service, host="localhost", port=9090, unix_socket=None,
                   proto_factory=TBinaryProtocolFactory(),
                   trans_factory=TBufferedTransportFactory(),
                   timeout=None):
    if unix_socket:
        socket = TSocket(unix_socket=unix_socket)
    elif host and port:
        socket = TSocket(host, port)
    else:
        raise ValueError("Either host/port or unix_socket must be provided.")

    if timeout:
        socket.set_timeout(timeout)

    try:

        transport = trans_factory.get_transport(socket)
        protocol = proto_factory.get_protocol(transport)
        transport.open()
        yield TClient(service, protocol)

    finally:
        transport.close()
