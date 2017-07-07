# -*- coding: utf-8 -*-

from __future__ import absolute_import

from os import path

import thriftpy
from thriftpy.contrib.async import make_client, make_server
from thriftpy.rpc import make_client as make_sync_client
from thriftpy.transport import TFramedTransportFactory

import pytest
import asyncio
import threading

addressbook = thriftpy.load(path.join(path.dirname(__file__),
                                      "addressbook.thrift"))


class Dispatcher(object):
    def __init__(self):
        self.registry = {}

    @asyncio.coroutine
    def add(self, person):
        """
        bool add(1: Person person);
        """
        if person.name in self.registry:
            return False
        self.registry[person.name] = person
        return True

    @asyncio.coroutine
    def get(self, name):
        """
        Person get(1: string name) throws (1: PersonNotExistsError not_exists);
        """
        if name not in self.registry:
            raise addressbook.PersonNotExistsError(
                'Person "{0}" does not exist!'.format(name))
        return self.registry[name]

    @asyncio.coroutine
    def remove(self, name):
        """
        bool remove(1: string name) throws (1: PersonNotExistsError not_exists)
        """
        # delay action for later
        yield from asyncio.sleep(.1)
        if name not in self.registry:
            raise addressbook.PersonNotExistsError(
                'Person "{0}" does not exist!'.format(name))
        del self.registry[name]
        return True


class Server(threading.Thread):
    def __init__(self):
        self.loop = loop = asyncio.new_event_loop()
        self.server = loop.run_until_complete(make_server(
            service=addressbook.AddressBookService,
            handler=Dispatcher(),
            loop=loop
        ))
        super().__init__()

    def run(self):
        loop = self.loop
        server = self.server
        asyncio.set_event_loop(loop)

        loop.run_forever()

        server.close()
        loop.run_until_complete(server.wait_closed())

        loop.close()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.join()


@pytest.fixture
def server():
    server = Server()
    server.start()
    yield server
    server.stop()


class TestAsyncClient:
    @pytest.fixture
    async def client(self, request, server):
        client = await make_client(addressbook.AddressBookService)
        request.addfinalizer(client.close)
        return client

    @pytest.mark.asyncio
    async def test_result(self, client):
        dennis = addressbook.Person(name='Dennis Ritchie')
        success = await client.add(dennis)
        assert success
        success = await client.add(dennis)
        assert not success
        person = await client.get(dennis.name)
        assert person.name == dennis.name

    @pytest.mark.asyncio
    async def test_exception(self, client):
        with pytest.raises(addressbook.PersonNotExistsError):
            await client.get('Brian Kernighan')


class TestSyncClient:
    @pytest.fixture
    async def client(self, request, server):
        client = make_sync_client(addressbook.AddressBookService,
                                  trans_factory=TFramedTransportFactory())
        request.addfinalizer(client.close)
        return client

    def test_result(self, client):
        dennis = addressbook.Person(name='Dennis Ritchie')
        success = client.add(dennis)
        assert success
        success = client.add(dennis)
        assert not success
        person = client.get(dennis.name)
        assert person.name == dennis.name

    def test_exception(self, client):
        with pytest.raises(addressbook.PersonNotExistsError):
            client.get('Brian Kernighan')
