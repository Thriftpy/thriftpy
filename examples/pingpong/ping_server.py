# -*- coding: utf-8 -*-

import thriftpy
from thriftpy.rpc import make_server

pingpong = thriftpy.load("pingpong.thrift")


class Dispatcher(object):
    def ping(self):
        print("ping pong!")
        return 'pong'


def main():
    server = make_server(pingpong.PingService, Dispatcher(), '127.0.0.1', 6000)
    print("serving...")
    server.serve()


if __name__ == '__main__':
    main()
