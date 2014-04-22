from thriftpy.protocol import TCyBinaryProtocolFactory
from thriftpy.thrift import TProcessor, TClient
from thriftpy.transport import TSocket, TBufferedTransport, TServerSocket
from thriftpy.server import TThreadedServer


def make_client(service, host, port, proto_factory=TCyBinaryProtocolFactory()):
    transport = TBufferedTransport(TSocket(host, port))
    protocol = proto_factory.get_protocol(transport)
    transport.open()
    return TClient(service, protocol)


def make_server(service, handler, host, port,
                proto_factory=TCyBinaryProtocolFactory()):
    processor = TProcessor(service, handler)
    transport = TServerSocket(host=host, port=port)
    server = TThreadedServer(processor, transport,
                             iprot_factory=proto_factory)
    return server
