from thriftpy.rpc import make_client

import example_thrift


def main():
    client = make_client(example_thrift.ExampleService, '127.0.0.1', 8000)
    print("ping() -> ", client.ping())
    print("hello('world') -> ", client.hello("world"))


if __name__ == "__main__":
    main()
