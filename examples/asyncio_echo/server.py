# -*- coding: utf-8 -*-
import asyncio
import thriftpy

from thriftpy.contrib.async.rpc import make_server

echo_thrift = thriftpy.load("echo.thrift", module_name="echo_thrift")


class Dispatcher(object):
    async def echo(self, param):
        print(param)
        await asyncio.sleep(0.1)
        return param


def main():
    server = make_server(echo_thrift.EchoService, Dispatcher(), '127.0.0.1', 6000)
    server.serve()


if __name__ == '__main__':
    main()
