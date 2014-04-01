from .transport import TMemoryBuffer
from .protocol import TBinaryProtocol


def serialize(thrift_object):
    transport = TMemoryBuffer()
    protocol = TBinaryProtocol(transport)
    thrift_object.write(protocol)
    return transport.getvalue()


def deserialize(thrift_object, buf):
    transport = TMemoryBuffer(buf)
    protocol = TBinaryProtocol(transport)
    thrift_object.read(protocol)
    return thrift_object


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
