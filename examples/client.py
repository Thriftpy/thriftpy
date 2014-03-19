from thriftpy.transport import TSocket, TBufferedTransport
from thriftpy.protocol import TBinaryProtocol

import example as example_thrift


def make_client(host, port):
    transport = TBufferedTransport(TSocket(host, port))
    protocol = TBinaryProtocol(transport)
    transport.open()
    return example_thrift.Client(protocol)


def main():
    client = make_client('127.0.0.1', 8000)
    print("ping() -> ", client.ping())
    print("hello('world') -> ", client.hello("world"))
    print("make(1, 'thrift') -> ", client.make(1, 'thrift'))


if __name__ == "__main__":
    main()
