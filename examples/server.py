from thriftpy.rpc import make_server

# import example as example_thrift
import example_thrift


class Dispatcher(object):
    def ping(self):
        return True

    def hello(self, name):
        return "Hello {}!".format(name)

    def make(self, id, name):
        return example_thrift.TItem(id=id, name=name)


def main():
    server = make_server(example_thrift.ExampleService, Dispatcher(),
                         '127.0.0.1', 8000)
    print("serving...")
    server.serve()


if __name__ == "__main__":
    main()
