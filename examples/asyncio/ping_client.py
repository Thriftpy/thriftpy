# -*- coding: utf-8 -*-

import thriftpy
from thriftpy.contrib.async import make_client

import asyncio


pp_thrift = thriftpy.load("pingpong.thrift", module_name="pp_thrift")

@asyncio.coroutine
def main():
    c = yield from make_client(pp_thrift.PingService)

    pong = yield from c.ping()
    print(pong)

    c.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
