# -*- coding: utf-8 -*-

import thriftpy
from thriftpy.rpc import client_context

pingpong = thriftpy.load("pingpong.thrift")


def main():
    with client_context(pingpong.PingService, '127.0.0.1', 8000) as c:
        pong = c.ping()
        print(pong)

if __name__ == '__main__':
    main()
