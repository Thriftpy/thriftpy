# -*- coding: utf-8 -*-


class Tracker(object):
    def pre_handle(header):
        raise NotImplementedError

    def handle(self, *args, **kwargs):
        raise NotImplementedError

    def gen_header(self, header):
        raise NotImplementedError
