from thriftpy.rpc import make_client

# import example as example_thrift
import example_thrift


def main():
    client = make_client(example_thrift.ExampleService, '127.0.0.1', 8000)
    print("ping() -> ", client.ping())
    print("hello('world') -> ", client.hello("world"))
    print("make(1, 'thrift') -> ", client.make(1, 'thrift'))


if __name__ == "__main__":
    main()
