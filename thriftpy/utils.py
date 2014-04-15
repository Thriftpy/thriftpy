from .transport import TMemoryBuffer
from .protocol import TBinaryProtocol


def serialize(thrift_object, proto=TBinaryProtocol):
    transport = TMemoryBuffer()
    protocol = proto(transport)
    thrift_object.write(protocol)
    return transport.getvalue()


def deserialize(thrift_object, buf, proto=TBinaryProtocol):
    transport = TMemoryBuffer(buf)
    protocol = proto(transport)
    thrift_object.read(protocol)
    return thrift_object
