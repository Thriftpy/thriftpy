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
        ctx.trace = {"header": header}

        header.server = self.server

    def gen_header(self, header):
        if hasattr(ctx, "trace"):
            cur_header = ctx.trace["header"]
            header.request_id = cur_header.request_id
            header.seq = cur_header.seq + 1
        else:
            header.request_id = str(uuid.uuid4())
            header.seq = 0

        header.client = self.client
        header.start = int(time.time() * 1000)

    def record_header(self, header):
        header.end = int(time.time() * 1000)
        self.record(header)

    def record(self, header):
        pass


class ConsoleTracker(TrackerBase):
    def record(self, header):
        print(header)
