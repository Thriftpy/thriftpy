# -*- coding: utf-8 -*-import warnings
import warnings
from .processor import TProcessor
from .protocol import TBinaryProtocolFactory
from .buffered import TBufferedTransportFactory
from .socket import TAsyncServerSocket
from .server import TAsyncServer


def make_server(service, handler,
                host="localhost", port=9090, unix_socket=None,
                proto_factory=TBinaryProtocolFactory(),
                trans_factory=TBufferedTransportFactory(),
                client_timeout=3000, certfile=None):
    processor = TProcessor(service, handler)

    if unix_socket:
        server_socket = TAsyncServerSocket(unix_socket=unix_socket)
        if certfile:
            warnings.warn("SSL only works with host:port, not unix_socket.")
    elif host and port:
        if certfile:
            # server_socket = TSSLServerSocket(
            #     host=host, port=port, client_timeout=client_timeout,
            #     certfile=certfile)
            pass
        else:
            server_socket = TAsyncServerSocket(
                host=host, port=port, client_timeout=client_timeout)
    else:
        raise ValueError("Either host/port or unix_socket must be provided.")

    server = TAsyncServer(processor, server_socket,
                          iprot_factory=proto_factory,
                          itrans_factory=trans_factory)
    return server
