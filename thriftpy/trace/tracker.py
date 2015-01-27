# -*- coding: utf-8 -*-


class Tracker(object):
    def handle(self, *args, **kwargs):
        raise NotImplementedError

    def gen_header(self, header):
        raise NotImplementedError
