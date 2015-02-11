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
        header.request_id = self.get_request_id()
        header.seq = (ctx.header.seq + 1) if hasattr(ctx, "header") else 0

        header.client = self.client
        header.server = self.server
        header.start = int(time.time() * 1000)

    def record(self, header, exception):
        pass

    def get_request_id(self):
        if hasattr(ctx, "header"):
            return ctx.header.request_id
        return str(uuid.uuid4())


class ConsoleTracker(TrackerBase):
    def record(self, header, exception):
        print(header)
