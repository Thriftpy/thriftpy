# -*- coding: utf-8 -*-

from __future__ import absolute_import

import multiprocessing
import socket
import time

import thriftpy
thriftpy.install_import_hook()

from thriftpy.rpc import make_server, client_context

import addressbook_thrift as addressbook


class Dispatcher(object):
    def __init__(self):
        self.ab = addressbook.AddressBook()
        self.ab.people = {}

    def ping(self):
        return True

    def add(self, person):
        self.ab.people[person.name] = person
        return True

    def remove(self, name):
        try:
            self.ab.people.pop(name)
            return True
        except KeyError:
            raise addressbook.PersonNotExistsError(
                "{} not exists".format(name))

    def get(self, name):
        try:
            return self.ab.people[name]
        except KeyError:
            raise addressbook.PersonNotExistsError(
                "{} not exists".format(name))

    def book(self):
        return self.ab

    def get_phonenumbers(self, name, count):
        p = [self.ab.people[name].phones[0]] if name in self.ab.people else []
        return p * count

    def get_phones(self, name):
        phone_numbers = self.ab.people[name].phones
        return {p.type: p.number for p in phone_numbers}

    def sleep(self, ms):
        time.sleep(ms / 1000.0)
        return True


def serve():
    server = make_server(addressbook.AddressBookService, Dispatcher(),
                         '127.0.0.1', 8000)
    server.serve()


def client(timeout=None):
    return client_context(addressbook.AddressBookService, '127.0.0.1', 8000,
                          timeout=timeout)


def rpc_client():
    # test void request
    with client() as c:
        assert c.ping() is None

    phone1 = addressbook.PhoneNumber()
    phone1.type = addressbook.PhoneType.MOBILE
    phone1.number = '555-1212'
    phone2 = addressbook.PhoneNumber()
    phone2.type = addressbook.PhoneType.HOME
    phone2.number = '555-1234'
    person = addressbook.Person()
    person.name = "Alice"
    person.phones = [phone1, phone2]
    person.created_at = int(time.time())

    # test put struct
    with client() as c:
        assert c.add(person)

    # test get struct
    with client() as c:
        alice = c.get("Alice")
        assert person == alice

    # test get complex struct
    with client() as c:
        # test get list
        # assert isinstance(c.get_phonenumbers("Alice"), list)

        # test get empty list
        assert len(c.get_phonenumbers("Alice", 0)) == 0
        assert len(c.get_phonenumbers("Alice", 1000)) == 1000

        # assert isinstance(c.get_phones("Alice"), dict)
        # assert isinstance(c.book(), addressbook.AddressBook)

    # test exception
    with client() as c:
        try:
            name = "Bob"
            c.remove(name)

            # should not be executed
            assert False

        except Exception as e:
            assert isinstance(e, addressbook.PersonNotExistsError)

    # test client timeout
    with client(timeout=500) as c:
        try:
            c.sleep(1000)

            # should not be executed
            assert False

        except Exception as e:
            assert isinstance(e, socket.timeout)


def test_rpc():
    p = multiprocessing.Process(target=serve)
    p.start()
    time.sleep(0.1)

    try:
        rpc_client()
    except:
        raise
    finally:
        p.terminate()


if __name__ == "__main__":
    test_rpc()
