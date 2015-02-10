# -*- coding: utf-8 -*-

import contextlib

from thriftpy import load
from thriftpy.transport import TSocket, TBufferedTransportFactory, \
    TTransportException, TServerSocket
from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.thrift import TTrackedClient, TTrackedProcessor, \
    TProcessorFactory, TProcessor
from thriftpy.server import TThreadedServer
from thriftpy.trace.tracker import ConsoleTracker

thrift = load("animal.thrift")
tracker = ConsoleTracker("tracker_client", "tracker_server")


class Server(TThreadedServer):
    def __init__(self, processor_factory, trans, trans_factory, prot_factory):
        self.daemon = False
        self.processor_factory = processor_factory
        self.trans = trans

        self.itrans_factory = self.otrans_factory = trans_factory
        self.iprot_factory = self.oprot_factory = prot_factory
        self.closed = False

    def handle(self, client):
        processor = self.processor_factory.get_processor()
        itrans = self.itrans_factory.get_transport(client)
        otrans = self.otrans_factory.get_transport(client)
        iprot = self.iprot_factory.get_protocol(itrans)
        oprot = self.oprot_factory.get_protocol(otrans)
        try:
            while True:
                processor.process(iprot, oprot)
        except TTransportException:
            pass
        except Exception:
            raise

        itrans.close()
        otrans.close()


@contextlib.contextmanager
def client(port=34567, client_class=TTrackedClient):
    socket = TSocket("localhost", port)
    trans = TBufferedTransportFactory().get_transport(socket)
    proto = TBinaryProtocolFactory().get_protocol(trans)
    trans.open()
    if client_class.__name__ == TTrackedClient.__name__:
        cli = client_class(tracker, thrift.Eating, proto)
    else:
        cli = client_class(thrift.Eating, proto)
    try:
        yield cli
    finally:
        trans.close()


def server(port=34567):
    processor = TProcessorFactory(thrift.Eating, Handler(), tracker,
                                  TTrackedProcessor)
    server_socket = TServerSocket(host="localhost", port=port)
    server = Server(processor, server_socket,
                    prot_factory=TBinaryProtocolFactory(),
                    trans_factory=TBufferedTransportFactory())
    return server


def server_not_tracked():
    processor = TProcessorFactory(thrift.Eating, Handler(), None,
                                  TProcessor)
    server_socket = TServerSocket(host="localhost", port=34567)
    server = Server(processor, server_socket,
                    prot_factory=TBinaryProtocolFactory(),
                    trans_factory=TBufferedTransportFactory())
    return server


class Handler(object):
    def ping(self):
        print('pong')

    def eat_grass(self, sh):
        grass = thrift.Grass()
        grass.name = "mary"
        grass.category = "plant"
        return grass

    def eat_sheep(self, lion):
        sheep = thrift.Sheep()
        sheep.name = "tom"
        sheep.age = 43
        with client(port=34568) as c:
            m = c.eat_grass(sheep)
            print(m)
        return sheep
