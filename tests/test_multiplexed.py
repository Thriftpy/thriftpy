# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import multiprocessing
import time

import pytest

import thriftpy
from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.rpc import client_context
from thriftpy.server import TThreadedServer
from thriftpy.thrift import TProcessor, TMultiplexingProcessor
from thriftpy.transport import TBufferedTransportFactory, TServerSocket


mux = thriftpy.load(os.path.join(os.path.dirname(__file__),
                                 "multiplexed.thrift"))
sock_path = "./thriftpy_test.sock"


class DispatcherOne(object):
    def doThingOne(self):
        return True


class DispatcherTwo(object):
    def doThingTwo(self):
        return True


@pytest.fixture(scope="module")
def server(request):
    p1 = TProcessor(mux.ThingOneService, DispatcherOne())
    p2 = TProcessor(mux.ThingTwoService, DispatcherTwo())

    mux_proc = TMultiplexingProcessor()
    mux_proc.register_processor(p1)
    mux_proc.register_processor(p2)

    _server = TThreadedServer(mux_proc, TServerSocket(unix_socket=sock_path),
                              iprot_factory=TBinaryProtocolFactory(),
                              itrans_factory=TBufferedTransportFactory())
    ps = multiprocessing.Process(target=_server.serve)
    ps.start()
    time.sleep(0.1)

    def fin():
        if ps.is_alive():
            ps.terminate()
        try:
            os.remove(sock_path)
        except IOError:
            pass
    request.addfinalizer(fin)


def client_one(timeout=3000):
    return client_context(mux.ThingOneService, unix_socket=sock_path,
                          timeout=timeout)


def client_two(timeout=3000):
    return client_context(mux.ThingTwoService, unix_socket=sock_path,
                          timeout=timeout)


def test_multiplexed_server(server):
    with client_one() as c:
        assert c.doThingOne() is True
    with client_two() as c:
        assert c.doThingTwo() is True
