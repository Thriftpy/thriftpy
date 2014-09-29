#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import thriftpy

thrift_service = thriftpy.load(os.path.join(os.path.dirname(__file__), "pingpong.thrift"), "pingpong_thrift")  # noqa
service = thrift_service.PingService


class PingpongServer(object):
    def ping(self):
        if os.environ.get('about_to_shutdown') == '1':
            raise service.AboutToShutDownException
        return "pong"

    def win(self):
        return "Yes, you win"


from thriftpy.thrift import TProcessor
app = TProcessor(service, PingpongServer())
