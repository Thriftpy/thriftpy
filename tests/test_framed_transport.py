# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import socket
import threading
import time

from os import path
from unittest import TestCase

from tornado import ioloop

import thriftpy
from thriftpy.tornado import make_server
from thriftpy.rpc import make_client
from thriftpy.transport.framed import TFramedTransportFactory
from thriftpy.protocol.binary import TBinaryProtocolFactory

from thriftpy._compat import CYTHON
logging.basicConfig(level=logging.INFO)

addressbook = thriftpy.load(path.join(path.dirname(__file__),
                                      "addressbook.thrift"))


class Dispatcher(object):
    def __init__(self, io_loop):
        self.io_loop = io_loop
        self.registry = {}

    def add(self, person):
        """
        bool add(1: Person person);
        """
        if person.name in self.registry:
            return False
        self.registry[person.name] = person
        return True

    def get(self, name):
        """
        Person get(1: string name)
        """
        if name not in self.registry:
            raise addressbook.PersonNotExistsError()
        return self.registry[name]


class FramedTransportTestCase(TestCase):
    TRANSPORT_FACTORY = TFramedTransportFactory()
    PROTOCOL_FACTORY = TBinaryProtocolFactory()

    def mk_server(self):
        self.io_loop = ioloop.IOLoop()
        server = make_server(addressbook.AddressBookService,
                             Dispatcher(self.io_loop), io_loop=self.io_loop)

        self.server = server
        sock = self.server_sock = socket.socket(socket.AF_INET,
                                                socket.SOCK_STREAM)
        sock.bind(('localhost', 0))
        sock.setblocking(0)
        self.port = sock.getsockname()[-1]
        self.server_thread = threading.Thread(target=self.listen)
        self.server_thread.setDaemon(True)
        self.server_thread.start()

    def listen(self):
        self.server_sock.listen(128)
        self.server.add_socket(self.server_sock)
        self.io_loop.start()

    def mk_client(self):
        return make_client(addressbook.AddressBookService,
                           '127.0.0.1', self.port,
                           proto_factory=self.PROTOCOL_FACTORY,
                           trans_factory=self.TRANSPORT_FACTORY)

    def setUp(self):
        self.mk_server()
        time.sleep(0.1)
        self.client = self.mk_client()

    def test_able_to_communicate(self):
        dennis = addressbook.Person(name='Dennis Ritchie')
        success = self.client.add(dennis)
        assert success
        success = self.client.add(dennis)
        assert not success

    def test_zero_length_string(self):
        dennis = addressbook.Person(name='')
        success = self.client.add(dennis)
        assert success
        success = self.client.get(name='')
        assert success


if CYTHON:
    from thriftpy.transport.framed import TCyFramedTransportFactory
    from thriftpy.protocol.cybin import TCyBinaryProtocolFactory

    class CyFramedTransportTestCase(FramedTransportTestCase):
        PROTOCOL_FACTORY = TCyBinaryProtocolFactory()
        TRANSPORT_FACTORY = TCyFramedTransportFactory()
