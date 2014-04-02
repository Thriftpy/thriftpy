from thriftpy.protocol import TBinaryProtocol
from thriftpy.thrift import TProcessor, TClient
from thriftpy.transport import TSocket, TBufferedTransport, TServerSocket
from thriftpy.server import TThreadedServer


def make_client(service, host, port):
    transport = TBufferedTransport(TSocket(host, port))
    protocol = TBinaryProtocol(transport)
    transport.open()
    return TClient(service, protocol)


def make_server(service, handler, host, port):
    processor = TProcessor(service, handler)
    transport = TServerSocket(host=host, port=port)
    server = TThreadedServer(processor, transport)
    return server
