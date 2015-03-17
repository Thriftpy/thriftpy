# -*- coding: utf-8 -*-

from __future__ import absolute_import

import contextlib
import os
import multiprocessing
import time
import tempfile
import pickle
import thriftpy

try:
    import dbm
except ImportError:
    import dbm.ndbm as dbm

import pytest

from thriftpy.contrib.tracking import TTrackedProcessor, TTrackedClient, \
    TrackerBase, trace_thrift
from thriftpy.contrib.tracking.tracker import ctx

from thriftpy.thrift import TProcessorFactory, TClient, TProcessor
from thriftpy.server import TThreadedServer
from thriftpy.transport import TServerSocket, TBufferedTransportFactory, \
    TTransportException, TSocket
from thriftpy.protocol import TBinaryProtocolFactory


addressbook = thriftpy.load(os.path.join(os.path.dirname(__file__),
                                         "addressbook.thrift"))
_, db_file = tempfile.mkstemp()


class SampleTracker(TrackerBase):
    def record(self, header, exception):
        db = dbm.open(db_file, 'w')

        key = "%s:%s" % (header.request_id, header.seq)
        db[key.encode("ascii")] = pickle.dumps(header.__dict__)
        db.close()

tracker = SampleTracker("test_client", "test_server")


class Dispatcher(object):
    def __init__(self):
        self.ab = addressbook.AddressBook()
        self.ab.people = {}

    def ping(self):
        return True

    def hello(self, name):
        return "hello %s" % name

    def remove(self, name):
        person = addressbook.Person(name="mary")
        with client(port=6098) as c:
            c.add(person)

        return True

    def get_phonenumbers(self, name, count):
        return [addressbook.PhoneNumber(number="sdaf"),
                addressbook.PhoneNumber(number='saf')]

    def add(self, person):
        with client(port=6099) as c:
            c.get_phonenumbers("jane", 1)

        with client(port=6099) as c:
            c.ping()
        return True

    def get(self, name):
        raise addressbook.PersonNotExistsError()


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


def gen_server(port=6029, tracker=tracker, processor=TTrackedProcessor):
    args = [processor, addressbook.AddressBookService, Dispatcher()]
    if tracker:
        args.insert(1, tracker)
    processor = TProcessorFactory(*args)
    server_socket = TServerSocket(host="localhost", port=port)
    server = TSampleServer(processor, server_socket,
                           prot_factory=TBinaryProtocolFactory(),
                           trans_factory=TBufferedTransportFactory())
    ps = multiprocessing.Process(target=server.serve)
    ps.start()
    return ps, server


@pytest.fixture
def server(request):
    ps, ser = gen_server()
    time.sleep(0.15)

    def fin():
        if ps.is_alive():
            ps.terminate()
    request.addfinalizer(fin)
    return ser


@pytest.fixture
def server1(request):
    ps, ser = gen_server(port=6098)
    time.sleep(0.15)

    def fin():
        if ps.is_alive():
            ps.terminate()
    request.addfinalizer(fin)
    return ser


@pytest.fixture
def server2(request):
    ps, ser = gen_server(port=6099)
    time.sleep(0.15)

    def fin():
        if ps.is_alive():
            ps.terminate()
    request.addfinalizer(fin)
    return ser


@pytest.fixture
def not_tracked_server(request):
    ps, ser = gen_server(port=6030, tracker=None, processor=TProcessor)
    time.sleep(0.15)

    def fin():
        if ps.is_alive():
            ps.terminate()
    request.addfinalizer(fin)
    return ser


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


@pytest.fixture
def dbm_db(request):
    db = dbm.open(db_file, 'n')
    db.close()

    def fin():
        try:
            os.remove(db_file)
        except OSError:
            pass
    request.addfinalizer(fin)


@pytest.fixture
def tracker_ctx(request):
    def fin():
        if hasattr(ctx, "header"):
            del ctx.header
        if hasattr(ctx, "counter"):
            del ctx.counter

    request.addfinalizer(fin)


def test_negotiation(server):
    with client() as c:
        assert c._upgraded is True


def test_tracker(server, dbm_db, tracker_ctx):
    with client() as c:
        c.ping()

    time.sleep(0.2)

    db = dbm.open(db_file, 'r')
    headers = list(db.keys())
    assert len(headers) == 1

    request_id = headers[0]
    data = pickle.loads(db[request_id])

    assert "start" in data and "end" in data
    data.pop("start")
    data.pop("end")

    assert data == {
        "request_id": request_id.decode("ascii").split(':')[0],
        "seq": '1',
        "client": "test_client",
        "server": "test_server",
        "api": "ping",
        "status": True
    }


def test_tracker_chain(server, server1, server2, dbm_db, tracker_ctx):
    with client() as c:
        c.remove("jane")
        c.hello("yes")

    time.sleep(0.2)

    db = dbm.open(db_file, 'r')
    headers = list(db.keys())
    assert len(headers) == 5

    headers = [pickle.loads(db[i]) for i in headers]
    headers.sort(key=lambda x: x["seq"])

    assert len(set([i["request_id"] for i in headers])) == 2

    seqs = [i["seq"] for i in headers]
    assert seqs == ['1', '1.1', '1.1.1', '1.1.2', '2']


def test_exception(server, dbm_db, tracker_ctx):
    with pytest.raises(addressbook.PersonNotExistsError):
        with client() as c:
            c.get("jane")

    db = dbm.open(db_file, 'r')
    headers = list(db.keys())
    assert len(headers) == 1

    header = pickle.loads(db[headers[0]])
    assert header["status"] is False


def test_not_tracked_client_tracked_server(server):
    with client(TClient) as c:
        c.ping()
        c.hello("world")


def test_tracked_client_not_tracked_server(not_tracked_server):
    with client(port=6030) as c:
        assert c._upgraded is False
        c.ping()
        c.hello("cat")
        a = c.get_phonenumbers("hello", 54)
        assert len(a) == 2
        assert a[0].number == 'sdaf' and a[1].number == 'saf'


def test_request_id_func():
    ctx.__dict__.clear()

    header = trace_thrift.RequestHeader()
    header.request_id = "hello"
    header.seq = 0

    tracker = TrackerBase()
    tracker.handle(header)

    header2 = trace_thrift.RequestHeader()
    tracker.gen_header(header2)
    assert header2.request_id == "hello"
