# -*- coding: utf-8 -*-

import thriftpy
from thriftpy.rpc import client_context
from thriftpy.protocol import (
    TBinaryProtocolFactory,
    TMultiplexingProtocolFactory
    )

dd_thrift = thriftpy.load("dingdong.thrift", module_name="dd_thrift")
pp_thrift = thriftpy.load("pingpong.thrift", module_name="pp_thrift")


def main():
    binary_factory = TBinaryProtocolFactory()
    dd_factory = TMultiplexingProtocolFactory(binary_factory, "dd_thrift")
    with client_context(dd_thrift.DingService, '127.0.0.1', 9090,
                        proto_factory=dd_factory) as c:
        # ring that doorbell
        dong = c.ding()
        print(dong)

    pp_factory = TMultiplexingProtocolFactory(binary_factory, "pp_thrift")
    with client_context(pp_thrift.PingService, '127.0.0.1', 9090,
                        proto_factory=pp_factory) as c:
        # play table tennis like a champ
        pong = c.ping()
        print(pong)


if __name__ == '__main__':
    main()
