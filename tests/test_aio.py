# -*- coding: utf-8 -*-
import os
import asyncio
# import uvloop
import threading

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

import time

import pytest

import thriftpy

thriftpy.install_import_hook()

from thriftpy.rpc import make_aio_server, make_aio_client
from thriftpy.transport import TTransportException

addressbook = thriftpy.load(os.path.join(os.path.dirname(__file__),
                                         "addressbook.thrift"))
unix_sock = "/tmp/thriftpy_test.sock"
SSL_PORT = 50441


class Dispatcher:
    def __init__(self):
        self.ab = addressbook.AddressBook()
        self.ab.people = {}

    @asyncio.coroutine
    def ping(self):
        return True

    @asyncio.coroutine
    def hello(self, name):
        return "hello " + name

    @asyncio.coroutine
    def add(self, person):
        self.ab.people[person.name] = person
        return True

    @asyncio.coroutine
    def remove(self, name):
        try:
            self.ab.people.pop(name)
            return True
        except KeyError:
            raise addressbook.PersonNotExistsError(
                "{0} not exists".format(name))

    @asyncio.coroutine
    def get(self, name):
        try:
            return self.ab.people[name]
        except KeyError:
            raise addressbook.PersonNotExistsError(
                "{0} not exists".format(name))

    @asyncio.coroutine
    def book(self):
        return self.ab

    @asyncio.coroutine
    def get_phonenumbers(self, name, count):
        p = [self.ab.people[name].phones[0]] if name in self.ab.people else []
        return p * count

    @asyncio.coroutine
    def get_phones(self, name):
        phone_numbers = self.ab.people[name].phones
        return dict((p.type, p.number) for p in phone_numbers)

    @asyncio.coroutine
    def sleep(self, ms):
        yield from asyncio.sleep(ms / 1000.0)
        return True


@pytest.fixture(scope="module")
def server(request):
    loop = asyncio.new_event_loop()
    server = make_aio_server(
        addressbook.AddressBookService,
        Dispatcher(),
        unix_socket=unix_sock,
        loop=loop
    )
    st = threading.Thread(target=server.serve)
    st.daemon = True
    st.start()
    time.sleep(0.01)


@pytest.fixture(scope="module")
def ssl_server(request):
    loop = asyncio.new_event_loop()
    ssl_server = make_aio_server(
        addressbook.AddressBookService, Dispatcher(),
        host='localhost', port=SSL_PORT,
        certfile="ssl/server.pem", keyfile="ssl/server.key", loop=loop
    )
    st = threading.Thread(target=ssl_server.serve)
    st.daemon = True
    st.start()
    time.sleep(0.01)


@pytest.fixture(scope="module")
def person():
    phone1 = addressbook.PhoneNumber()
    phone1.type = addressbook.PhoneType.MOBILE
    phone1.number = '555-1212'
    phone2 = addressbook.PhoneNumber()
    phone2.type = addressbook.PhoneType.HOME
    phone2.number = '555-1234'

    # empty struct
    phone3 = addressbook.PhoneNumber()

    alice = addressbook.Person()
    alice.name = "Alice"
    alice.phones = [phone1, phone2, phone3]
    alice.created_at = int(time.time())

    return alice


async def client(timeout=3000):
    return await make_aio_client(
        addressbook.AddressBookService,
        unix_socket=unix_sock, socket_timeout=timeout
    )


async def ssl_client(timeout=3000):
    return await make_aio_client(
        addressbook.AddressBookService,
        host='localhost', port=SSL_PORT,
        socket_timeout=timeout,
        cafile="ssl/CA.pem", certfile="ssl/client.crt",
        keyfile="ssl/client.key", server_hostname='localhost')


@pytest.mark.asyncio
async def test_void_api(server):
    c = await client()
    assert await c.ping() is None
    c.close()


@pytest.mark.asyncio
async def test_void_api_with_ssl(ssl_server):
    c = await ssl_client()
    assert await c.ping() is None
    c.close()


@pytest.mark.asyncio
async def test_string_api(server):
    c = await client()
    assert await c.hello("world") == "hello world"
    c.close()


@pytest.mark.asyncio
async def test_string_api_with_ssl(ssl_server):
    c = await client()
    assert await c.hello("world") == "hello world"
    c.close()


@pytest.mark.asyncio
async def test_huge_res(server):
    c = await client()
    big_str = "world" * 100000
    assert await c.hello(big_str) == "hello " + big_str
    c.close()


@pytest.mark.asyncio
async def test_huge_res_with_ssl(ssl_server):
    c = await ssl_client()
    big_str = "world" * 100000
    assert await c.hello(big_str) == "hello " + big_str
    c.close()


@pytest.mark.asyncio
async def test_tstruct_req(person):
    c = await client()
    assert await c.add(person) is True
    c.close()


@pytest.mark.asyncio
async def test_tstruct_req_with_ssl(person):
    c = await ssl_client()
    assert await c.add(person) is True
    c.close()


@pytest.mark.asyncio
async def test_tstruct_res(person):
    c = await client()
    assert person == await c.get("Alice")
    c.close()


@pytest.mark.asyncio
async def test_tstruct_res_with_ssl(person):
    c = await ssl_client()
    assert person == await c.get("Alice")
    c.close()


@pytest.mark.asyncio
async def test_complex_tstruct():
    c = await client()
    assert len(await c.get_phonenumbers("Alice", 0)) == 0
    assert len(await c.get_phonenumbers("Alice", 1000)) == 1000
    c.close()


@pytest.mark.asyncio
async def test_complex_tstruct_with_ssl():
    c = await ssl_client()
    assert len(await c.get_phonenumbers("Alice", 0)) == 0
    assert len(await c.get_phonenumbers("Alice", 1000)) == 1000
    c.close()


@pytest.mark.asyncio
async def test_exception():
    with pytest.raises(addressbook.PersonNotExistsError):
        c = await client()
        await c.remove("Bob")


@pytest.mark.asyncio
async def test_exception_iwth_ssl():
    with pytest.raises(addressbook.PersonNotExistsError):
        c = await ssl_client()
        await c.remove("Bob")


@pytest.mark.asyncio
async def test_client_socket_timeout():
    with pytest.raises(asyncio.TimeoutError):
        try:
            c = await ssl_client(timeout=500)
            await c.sleep(1000)
        except:
            c.close()
            raise


@pytest.mark.asyncio
async def test_ssl_socket_timeout():
    # SSL socket timeout raises socket.timeout since Python 3.2.
    # http://bugs.python.org/issue10272
    with pytest.raises(asyncio.TimeoutError):
        try:
            c = await ssl_client(timeout=500)
            await c.sleep(1000)
        except:
            c.close()
            raise


@pytest.mark.asyncio
async def test_client_connect_timeout():
    with pytest.raises(TTransportException):
        c = await make_aio_client(
            addressbook.AddressBookService,
            unix_socket='/tmp/test.sock',
            connect_timeout=1000
        )
        await c.hello('test')
