# -*- coding: utf-8 -*-

import thriftpy

from thriftpy.rpc import make_client

sleep_thrift = thriftpy.load("sleep.thrift", module_name="sleep_thrift")


def main():
    client = make_client(sleep_thrift.Sleep, '127.0.0.1', 6000)
    # sleep multiple times, but the client won't wait any more
    client.sleep(1)
    client.sleep(2)
    client.sleep(3)
    client.sleep(4)


if __name__ == '__main__':
    main()
