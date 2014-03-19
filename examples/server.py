from thriftpy.transport import TServerSocket
from thriftpy.server import TThreadedServer

import example as example_thrift


class Dispatcher(object):
    def ping(self):
        return True

    def hello(self, name):
        return "Hello {}!".format(name)

    def make(self, id, name):
        return example_thrift.TItem(id=id, name=name)


def make_server(host, port):
    processor = example_thrift.Processor(Dispatcher())
    transport = TServerSocket(host=host, port=port)
    server = TThreadedServer(processor, transport)
    return server


def main():
    server = make_server('127.0.0.1', 8000)
    print("serving...")
    server.serve()


if __name__ == "__main__":
    main()
