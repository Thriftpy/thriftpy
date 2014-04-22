from .transport import TMemoryBuffer
from .protocol import TCyBinaryProtocolFactory


def serialize(thrift_object, proto_factory=TCyBinaryProtocolFactory()):
    transport = TMemoryBuffer()
    protocol = proto_factory.get_protocol(transport)
    thrift_object.write(protocol)
    return transport.getvalue()


def deserialize(thrift_object, buf, proto_factory=TCyBinaryProtocolFactory()):
    transport = TMemoryBuffer(buf)
    protocol = proto_factory.get_protocol(transport)
    thrift_object.read(protocol)
    return thrift_object


def hexlify(byte_array, delimeter=' '):
    return delimeter.join(map(lambda x: format(x, '02x'), byte_array))


def hexprint(byte_array, delimeter=' ', count=10):
    print("Bytes:")
    print(byte_array)

    print("\nHex:")
    g = hexlify(byte_array, delimeter).split(delimeter)
    print('\n'.join(' '.join(g[i:i+10]) for i in range(0, len(g), 10)))
