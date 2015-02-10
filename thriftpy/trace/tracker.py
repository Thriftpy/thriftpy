# -*- coding: utf-8 -*-

import threading
import time
import uuid

ctx = threading.local()


class TrackerBase(object):
    def __init__(self, client=None, server=None):
        self.client = client
        self.server = server

    def handle(self, header):
        ctx.header = header

    def gen_header(self, header):
        if hasattr(ctx, "header"):
            cur_header = ctx.header
            header.request_id = cur_header.request_id
            header.seq = cur_header.seq + 1
        else:
            header.request_id = str(uuid.uuid4())
            header.seq = 0

        header.client = self.client
        header.server = self.server
        header.start = int(time.time() * 1000)

    def record(self, header, exception):
        pass


class ConsoleTracker(TrackerBase):
    def record(self, header, exception):
        print(header)
