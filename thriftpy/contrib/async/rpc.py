# -*- coding: utf-8 -*-import warnings
import asyncio
import warnings
from .processor import TAsyncProcessor
from .client import TAsyncClient
from .protocol import TAsyncBinaryProtocolFactory
from .buffered import TAsyncBufferedTransportFactory
from .socket import TAsyncSocket, TAsyncServerSocket
from .server import TAsyncServer


@asyncio.coroutine
def make_client(service, host="localhost", port=9090, unix_socket=None,
                proto_factory=TAsyncBinaryProtocolFactory(),
                trans_factory=TAsyncBufferedTransportFactory(),
                timeout=None,
                cafile=None, ssl_context=None, certfile=None, keyfile=None):
    if unix_socket:
        socket = TAsyncSocket(unix_socket=unix_socket)
        if certfile:
            warnings.warn("SSL only works with host:port, not unix_socket.")
    elif host and port:
            socket = TAsyncSocket(host, port, socket_timeout=timeout)
    else:
        raise ValueError("Either host/port or unix_socket must be provided.")

    transport = trans_factory.get_transport(socket)
    protocol = proto_factory.get_protocol(transport)
    yield from transport.open()
    return TAsyncClient(service, protocol)


def make_server(service, handler,
                host="localhost", port=9090, unix_socket=None,
                proto_factory=TAsyncBinaryProtocolFactory(),
                trans_factory=TAsyncBufferedTransportFactory(),
                client_timeout=3000, certfile=None, keyfile=None, ssl_context=None):
    processor = TAsyncProcessor(service, handler)

    if unix_socket:
        server_socket = TAsyncServerSocket(unix_socket=unix_socket)
        if certfile:
            warnings.warn("SSL only works with host:port, not unix_socket.")
    elif host and port:
            server_socket = TAsyncServerSocket(
                host=host, port=port,
                client_timeout=client_timeout,
                certfile=certfile, keyfile=keyfile, ssl_context=ssl_context)
    else:
        raise ValueError("Either host/port or unix_socket must be provided.")

    server = TAsyncServer(processor, server_socket,
                          iprot_factory=proto_factory,
                          itrans_factory=trans_factory)
    return server
