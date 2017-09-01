# -*- coding: utf-8 -*-
import thriftpy

from thriftpy.rpc import client_context

echo_thrift = thriftpy.load("echo.thrift", module_name="echo_thrift")


def main():
    with client_context(echo_thrift.PingService, '127.0.0.1', 6000) as c:
        pong = c.ping('echo')
        print(pong)


if __name__ == '__main__':
    main()
