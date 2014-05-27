# -*- coding: utf-8 -*-

from thriftpy.rpc import client_context

import pingpong_thrift as pingpong


def main():
    with client_context(pingpong.PingService, '127.0.0.1', 6000) as c:
        pong = c.ping()
        print(pong)


if __name__ == '__main__':
    main()
