from __future__ import absolute_import
from thriftpy.tornado import make_server
from thriftpy.rpc import make_client
from thriftpy.transport import TFramedTransportFactory
from tornado import ioloop
from unittest import TestCase
from os import path

import logging
import thriftpy
import threading
import socket
import time


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


class FramedTransportTestCase(TestCase):
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
                           transport_factory=TFramedTransportFactory())

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
