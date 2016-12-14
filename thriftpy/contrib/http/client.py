# -*- coding: utf-8 -*-

import contextlib
import time

from thriftpy.thrift import TClient
from thriftpy.contrib.tracking import track_thrift, RequestInfo
from thriftpy.contrib.tracking import TrackerBase


class Client(TClient):
    def __init__(self, service_name, tracker_handler, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

        self.tracker = tracker_handler
        self.service_name = service_name

    def _send(self, _api, **kwargs):
        self._header = track_thrift.RequestHeader()
        self.tracker.gen_header(self._header)

        soa = {"req": self._header.request_id, "rpc": self._header.seq}
        self._oprot.write_metadata(soa=soa, iface=self.service_name)

        self.send_start = int(time.time() * 1000)
        super(Client, self)._send(_api, **kwargs)

    def _req(self, _api, *args, **kwargs):
        exception, status = None, False

        try:
            res = super(Client, self)._req(_api, *args, **kwargs)
            status = True
            return res
        except BaseException as e:
            exception = e
            raise
        finally:
            header_info = RequestInfo(
                request_id=self._header.request_id,
                seq=self._header.seq,
                client=self.tracker.client,
                server=self.tracker.server,
                api=_api,
                status=status,
                start=self.send_start,
                end=int(time.time() * 1000),
                annotation=self.tracker.annotation
            )
            self.tracker.record(header_info, exception)


@contextlib.contextmanager
def client_ctx(host, port, service, package_name, timeout=20, tracker=None,
               keep_alive=True):
    from thriftpy.transport import TSocket, TBufferedTransport
    from thriftpy.contrib.http import Client, THTTPJsonProtocol

    socket = TSocket(host, port)
    socket.set_timeout(timeout)

    trans = TBufferedTransport(socket)
    proto = THTTPJsonProtocol(trans, keep_alive=keep_alive)
    trans.open()

    if tracker is None:
        tracker = TrackerBase("http_client", "unknown")

    service_name = "%s.%s" % (package_name, service.__name__)
    client = Client(service_name, tracker, service, proto)

    try:
        yield client
    finally:
        trans.close()
