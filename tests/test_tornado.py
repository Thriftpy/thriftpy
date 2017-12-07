# -*- coding: utf-8 -*-

from __future__ import absolute_import

from os import path
import logging
import socket

from tornado import gen, testing

import thriftpy
from thriftpy.tornado import make_client
from thriftpy.tornado import make_server


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
        Person get(1: string name) throws (1: PersonNotExistsError not_exists);
        """
        if name not in self.registry:
            raise addressbook.PersonNotExistsError(
                'Person "{}" does not exist!'.format(name))
        return self.registry[name]

    @gen.coroutine
    def remove(self, name):
        """
        bool remove(1: string name) throws (1: PersonNotExistsError not_exists)
        """
        # delay action for later
        yield gen.Task(self.io_loop.add_callback)
        if name not in self.registry:
            raise addressbook.PersonNotExistsError(
                'Person "{}" does not exist!'.format(name))
        del self.registry[name]
        raise gen.Return(True)


class TornadoRPCTestCase(testing.AsyncTestCase):
    def mk_server(self):
        server = make_server(addressbook.AddressBookService,
                             Dispatcher(self.io_loop),
                             io_loop=self.io_loop)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))
        sock.setblocking(0)
        sock.listen(128)

        server.add_socket(sock)
        self.port = sock.getsockname()[-1]
        return server

    def mk_client(self):
        return make_client(addressbook.AddressBookService,
                           '127.0.0.1', self.port, io_loop=self.io_loop)

    def setUp(self):
        super(TornadoRPCTestCase, self).setUp()
        self.server = self.mk_server()
        self.client = self.io_loop.run_sync(self.mk_client)

    def tearDown(self):
        self.server.stop()
        self.client.close()
        super(TornadoRPCTestCase, self).tearDown()

    @testing.gen_test
    def test_synchronous_result(self):
        dennis = addressbook.Person(name='Dennis Ritchie')
        success = yield self.client.add(dennis)
        assert success
        success = yield self.client.add(dennis)
        assert not success
        person = yield self.client.get(dennis.name)
        assert person.name == dennis.name

    @testing.gen_test
    def test_synchronous_exception(self):
        exc = None
        try:
            yield self.client.get('Brian Kernighan')
        except Exception as e:
            exc = e

        assert isinstance(exc, addressbook.PersonNotExistsError)

    @testing.gen_test
    def test_asynchronous_result(self):
        dennis = addressbook.Person(name='Dennis Ritchie')
        yield self.client.add(dennis)
        success = yield self.client.remove(dennis.name)
        assert success

    @testing.gen_test
    def test_asynchronous_exception(self):
        exc = None
        try:
            yield self.client.remove('Brian Kernighan')
        except Exception as e:
            exc = e
        assert isinstance(exc, addressbook.PersonNotExistsError)
