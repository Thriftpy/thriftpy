# -*- coding: utf-8 -*-

import thriftpy
pp_thrift = thriftpy.load("pingpong.thrift", module_name="pp_thrift")

from thriftpy.rpc import client_context


def main():
    with client_context(pp_thrift.PingService, '127.0.0.1', 6000) as c:
        pong = c.ping()
        print(pong)


if __name__ == '__main__':
    main()
