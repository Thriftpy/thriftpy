from thriftpy.thrift import (
    TPayload,
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
        3: (TType.I32, "created_at"),
    }


class AddressBook(TPayload):
    thrift_spec = {
        1: (TType.MAP, "people", (TType.STRING, (TType.STRUCT, Person)))
    }


class AddressBookService(object):
    thrift_services = [
        "ping",
        "add",
        "del",
        "get",
    ]

    class ping_args(TPayload):
        thrift_spec = {
        }

    class ping_result(TPayload):
        thrift_spec = {
            0: (TType.BOOL, "success"),
        }

    class add_args(TPayload):
        thrift_spec = {
            1: (TType.STRUCT, "person", Person),
        }

    class add_result(TPayload):
        thrift_spec = {
            0: (TType.BOOL, "success"),
        }

    class del_args(TPayload):
        thrift_spec = {
            1: (TType.STRING, "name"),
        }

    class del_result(TPayload):
        thrift_spec = {
            0: (TType.BOOL, "success"),
        }

    class get_args(TPayload):
        thrift_spec = {}

    class get_result(TPayload):
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
