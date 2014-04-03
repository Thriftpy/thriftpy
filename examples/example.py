from thriftpy.thrift import (
    TPayload,
    TType,
)

DEFAULT = 10
MAX = 200


class MessageStatus(object):
    VALID = 0
    INVALID = 1


class TItem(TPayload):
    thrift_spec = {
        1: (TType.I32, 'id'),
        2: (TType.STRING, 'name'),
    }


class ExampleService(object):
    thrift_services = [
        "ping",
        "hello",
        "make",
    ]

    class ping_args(TPayload):
        thrift_spec = {
        }

    class ping_result(TPayload):
        thrift_spec = {
            0: (TType.BOOL, 'success'),
        }

    class hello_args(TPayload):
        thrift_spec = {1: (TType.STRING, 'name')}

    class hello_result(TPayload):
        thrift_spec = {
            0: (TType.STRING, 'success'),
        }

    class make_args(TPayload):
        thrift_spec = {
            1: (TType.I32, 'id'),
            2: (TType.STRING, 'name')
        }

    class make_result(TPayload):
        thrift_spec = {
            0: (TType.STRUCT, 'success', TItem),
        }
