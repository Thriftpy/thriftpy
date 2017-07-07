# -*- coding: utf-8 -*-

import thriftpy
import asyncio
from thriftpy.contrib.async import make_server


pp_thrift = thriftpy.load("pingpong.thrift", module_name="pp_thrift")


class Dispatcher(object):
    @asyncio.coroutine
    def ping(self):
        print("ping pong!")
        return 'pong'

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(
        make_server(pp_thrift.PingService, Dispatcher()))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
