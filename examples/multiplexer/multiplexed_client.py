# -*- coding: utf-8 -*-

import thriftpy
from thriftpy.rpc import client_context

dd_thrift = thriftpy.load("dingdong.thrift", module_name="dd_thrift")
pp_thrift = thriftpy.load("pingpong.thrift", module_name="pp_thrift")


def main():
    with client_context(dd_thrift.DingService, '127.0.0.1', 9090) as c:
        # ring that doorbell
        dong = c.ding()
        print(dong)

    with client_context(pp_thrift.PingService, '127.0.0.1', 9090) as c:
        # play table tennis like a champ
        pong = c.ping()
        print(pong)


if __name__ == '__main__':
    main()
