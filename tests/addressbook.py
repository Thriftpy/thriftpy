"""This file is a demo for what the dynamiclly generated code would be like.
"""

from thriftpy.thrift import (
    TPayload,
    TException,
    TType,
)

DEFAULT_LIST_SIZE = 10


class PhoneType(object):
    MOBILE = 0
    HOME = 1
    WORK = 2


class PhoneNumber(TPayload):
    thrift_spec = {
        1: (TType.I32, "type"),
        2: (TType.STRING, "number"),
    }


class Person(TPayload):
    thrift_spec = {
        1: (TType.STRING, "name"),
        2: (TType.LIST, "phones", (TType.STRUCT, PhoneNumber)),
        4: (TType.I32, "created_at"),
    }


class AddressBook(TPayload):
    thrift_spec = {
        1: (TType.MAP, "people",
            (TType.STRING, (TType.STRUCT, Person)))
    }


class PersonNotExistsError(TException):
    thrift_spec = {
        1: (TType.STRING, "message")
    }


class AddressBookService(object):
    thrift_services = [
        "ping",
        "add",
        "remove",
        "get",
        "book",
        "get_phones",
    ]

    class ping_args(TPayload):
        thrift_spec = {}

    class ping_result(TPayload):
        thrift_spec = {}

    class add_args(TPayload):
        thrift_spec = {
            1: (TType.STRUCT, "person", Person),
        }

    class add_result(TPayload):
        thrift_spec = {
            0: (TType.BOOL, "success"),
        }

    class remove_args(TPayload):
        thrift_spec = {
            1: (TType.STRING, "name"),
        }

    class remove_result(TPayload):
        thrift_spec = {
            0: (TType.BOOL, "success"),
            1: (TType.STRUCT, "not_exists", PersonNotExistsError)
        }

    class get_args(TPayload):
        thrift_spec = {
            1: (TType.STRING, "name"),
        }

    class get_result(TPayload):
        thrift_spec = {
            0: (TType.STRUCT, "success", Person),
        }

    class book_args(TPayload):
        thrift_spec = {}

    class book_result(TPayload):
        thrift_spec = {
            0: (TType.STRUCT, "success", AddressBook),
        }

    class get_phones_args(TPayload):
        thrift_spec = {
            1: (TType.STRING, "name"),
        }

    class get_phones_result(TPayload):
        thrift_spec = {
            0: (TType.MAP, "success", (TType.I32, TType.STRING)),
        }
