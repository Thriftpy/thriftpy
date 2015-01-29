# -*- coding: utf-8 -*-

from __future__ import absolute_import

import contextlib
import os
import multiprocessing
import time
import tempfile
import pickle
import uuid

try:
    import dbm
except ImportError:
    import dbm.ndbm as dbm

import pytest

import thriftpy

from thriftpy.transport import TServerSocket, TBufferedTransportFactory, \
    TTransportException, TSocket
from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.thrift import TTrackedProcessor, TTrackedClient, \
    TProcessorFactory, TClient, TProcessor
from thriftpy.server import TThreadedServer
from thriftpy.trace.tracker import Tracker


addressbook = thriftpy.load(os.path.join(os.path.dirname(__file__),
                                         "addressbook.thrift"))
request_id = str(uuid.uuid4())
_, db_file = tempfile.mkstemp()


class SampleTracker(Tracker):
    def pre_handle(self, header):
        pass

    def handle(self, header, status):
        db = dbm.open(db_file, 'w')

        header.seq += 1
        header.server = "test_server"
        header.end = int(time.time() * 1000)
        header.status = status

        db[header.request_id.encode("ascii")] = pickle.dumps(header.__dict__)
        db.close()

    def gen_header(self, header):
        header.request_id = request_id
        header.client = "test_client"
        header.parent_id = ''
        header.start = int(time.time() * 1000)
        header.seq = 0

tracker = SampleTracker()


class Dispatcher(object):
    def __init__(self):
        self.ab = addressbook.AddressBook()
        self.ab.people = {}

    def ping(self):
        return True

    def hello(self, name):
        return "hello %s" % name


class TSampleServer(TThreadedServer):
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


@pytest.fixture(scope="module")
def server(request):
    processor = TProcessorFactory(addressbook.AddressBookService, Dispatcher(),
                                  tracker, TTrackedProcessor)
    server_socket = TServerSocket(host="localhost", port=6029)
    server = TSampleServer(processor, server_socket,
                           prot_factory=TBinaryProtocolFactory(),
                           trans_factory=TBufferedTransportFactory())
    ps = multiprocessing.Process(target=server.serve)
    ps.start()

    time.sleep(0.5)

    def fin():
        if ps.is_alive():
            ps.terminate()
    request.addfinalizer(fin)

    return server


@pytest.fixture(scope="module")
def not_tracked_server(request):
    processor = TProcessorFactory(addressbook.AddressBookService, Dispatcher(),
                                  None, TProcessor)
    server_socket = TServerSocket(host="localhost", port=6030)
    server = TSampleServer(processor, server_socket,
                           prot_factory=TBinaryProtocolFactory(),
                           trans_factory=TBufferedTransportFactory())
    ps = multiprocessing.Process(target=server.serve)
    ps.start()

    time.sleep(0.5)

    def fin():
        if ps.is_alive():
            ps.terminate()
    request.addfinalizer(fin)

    return server


@contextlib.contextmanager
def client(client_class=TTrackedClient, port=6029):
    socket = TSocket("localhost", port)

    try:
        trans = TBufferedTransportFactory().get_transport(socket)
        proto = TBinaryProtocolFactory().get_protocol(trans)
        trans.open()
        args = [addressbook.AddressBookService, proto]
        if client_class.__name__ == TTrackedClient.__name__:
            args.insert(0, tracker)
        yield client_class(*args)
    finally:
        trans.close()


@pytest.fixture(scope="module")
def dbm_db(request):
    db = dbm.open(db_file, 'n')
    db.close()

    def fin():
        try:
            os.remove(db_file)
        except IOError:
            pass
    request.addfinalizer(fin)


def test_negotiation(server):
    with client() as c:
        assert c._upgraded is True


def test_tracker(server, dbm_db):
    with client() as c:
        c.ping()

    time.sleep(0.6)

    db = dbm.open(db_file, 'r')
    headers = list(db.keys())
    assert len(headers) == 1

    data = pickle.loads(db[headers[0]])
    data.pop("start")
    data.pop("end")

    assert data == {
        "request_id": request_id,
        "seq": 1,
        "parent_id": '',
        "client": "test_client",
        "server": "test_server",
        "status": True
    }


def test_not_tracked_client_tracked_server(server):
    with client(TClient) as c:
        c.ping()
        c.hello("world")


def test_tracked_client_not_tracked_server(not_tracked_server):
    with client(port=6030) as c:
        assert c._upgraded is False
        c.ping()
        c.hello("cat")
