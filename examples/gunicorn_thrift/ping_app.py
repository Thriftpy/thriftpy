# -*- coding: utf-8 -*-

import thriftpy
from thriftpy.thrift import TProcessor

pingpong = thriftpy.load("pingpong.thrift")


class Dispatcher(object):
    def ping(self):
        print("ping pong!")
        return 'pong'

app = TProcessor(pingpong.PingService, Dispatcher())
