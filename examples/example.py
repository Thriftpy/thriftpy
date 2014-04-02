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
        1: (TType.I32, 'id', None, None),
        2: (TType.STRING, 'name', None, None),
    }


class TService(object):
    thrift_services = [
        "ping",
        "hello",
    ]

    class ping_args(TPayload):
        thrift_spec = {
        }

    class ping_result(TPayload):
        thrift_spec = {
            0: (TType.BOOL, 'success', None, None),
        }

    class hello_args(TPayload):
        thrift_spec = {
            1: (TType.STRING, 'name', None, None, )
        }

    class hello_result(TPayload):
        thrift_spec = {
            0: (TType.STRING, 'success', None, None),
        }
