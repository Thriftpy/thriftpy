# -*- coding: utf-8 -*-
import thriftpy
import asyncio
from thriftpy.rpc import make_async_client


echo_thrift = thriftpy.load("echo.thrift", module_name="echo_thrift")


async def main():
    client = await make_async_client(
        echo_thrift.EchoService, '127.0.0.1', 6000)
    print(await client.echo('hello, world'))
    client.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
