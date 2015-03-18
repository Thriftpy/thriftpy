# -*- coding: utf-8 -*-

"""
Tracking support similar to twitter finagle-thrift.

Note: When using tracking, every client should have a corresponding
server processor.
"""

from __future__ import absolute_import

import os.path
import time

from ...thrift import TClient, TApplicationException, TMessageType, \
    TProcessor, TType
from ...parser import load

trace_method = "__thriftpy_tracing_method_name__v2"
trace_thrift = load(os.path.join(os.path.dirname(__file__), "tracking.thrift"))


__all__ = ["TTrackedClient", "TTrackedProcessor", "TrackerBase",
           "ConsoleTracker"]


class TTrackedClient(TClient):
    def __init__(self, tracker_handler, *args, **kwargs):
        super(TTrackedClient, self).__init__(*args, **kwargs)

        self.tracer = tracker_handler
        self._upgraded = False

        try:
            self._negotiation()
            self._upgraded = True
        except TApplicationException as e:
            if e.type != TApplicationException.UNKNOWN_METHOD:
                raise

    def _negotiation(self):
        self._oprot.write_message_begin(trace_method, TMessageType.CALL,
                                        self._seqid)
        args = trace_thrift.UpgradeArgs()
        args.write(self._oprot)
        self._oprot.write_message_end()
        self._oprot.trans.flush()

        api, msg_type, seqid = self._iprot.read_message_begin()
        if msg_type == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(self._iprot)
            self._iprot.read_message_end()
            raise x
        else:
            result = trace_thrift.UpgradeReply()
            result.read(self._iprot)
            self._iprot.read_message_end()

    def _send(self, _api, **kwargs):
        if self._upgraded:
            self._header = trace_thrift.RequestHeader()
            self.tracer.gen_header(self._header)
            self._header.write(self._oprot)

        self.send_start = int(time.time() * 1000)
        super(TTrackedClient, self)._send(_api, **kwargs)

    def _req(self, _api, *args, **kwargs):
        if not self._upgraded:
            return super(TTrackedClient, self)._req(_api, *args, **kwargs)

        exception = None
        status = False

        try:
            res = super(TTrackedClient, self)._req(_api, *args, **kwargs)
            status = True
            return res
        except BaseException as e:
            exception = e
            raise
        finally:
            header_info = trace_thrift.RequestInfo(
                request_id=self._header.request_id,
                seq=self._header.seq,
                client=self.tracer.client,
                server=self.tracer.server,
                api=_api,
                status=status,
                start=self.send_start,
                end=int(time.time() * 1000)
            )
            self.tracer.record(header_info, exception)


class TTrackedProcessor(TProcessor):
    def __init__(self, tracker_handler, *args, **kwargs):
        super(TTrackedProcessor, self).__init__(*args, **kwargs)

        self.tracer = tracker_handler
        self._upgraded = False

    def process(self, iprot, oprot):
        if not self._upgraded:
            res = self._try_upgrade(iprot)
        else:
            request_header = trace_thrift.RequestHeader()
            request_header.read(iprot)
            self.tracer.handle(request_header)
            res = super(TTrackedProcessor, self).process_in(iprot)

        self._do_process(iprot, oprot, *res)

    def _try_upgrade(self, iprot):
        api, msg_type, seqid = iprot.read_message_begin()
        if msg_type == TMessageType.CALL and api == trace_method:
            self._upgraded = True

            args = trace_thrift.UpgradeArgs()
            args.read(iprot)
            result = trace_thrift.UpgradeReply()
            result.oneway = False

            def call():
                pass
            iprot.read_message_end()
        else:
            result, call = self._process_in(api, iprot)

        return api, seqid, result, call

    def _process_in(self, api, iprot):
        if api not in self._service.thrift_services:
            iprot.skip(TType.STRUCT)
            iprot.read_message_end()
            return TApplicationException(
                TApplicationException.UNKNOWN_METHOD), None

        args = getattr(self._service, api + "_args")()
        args.read(iprot)
        iprot.read_message_end()
        result = getattr(self._service, api + "_result")()

        # convert kwargs to args
        api_args = [args.thrift_spec[k][1]
                    for k in sorted(args.thrift_spec)]

        def call():
            return getattr(self._handler, api)(
                *(args.__dict__[k] for k in api_args)
            )

        return result, call

    def _do_process(self, iprot, oprot, api, seqid, result, call):
        if isinstance(result, TApplicationException):
            return self.send_exception(oprot, api, result, seqid)

        try:
            result.success = call()
        except Exception as e:
            # raise if api don't have throws
            self.handle_exception(e, result)

        if not result.oneway:
            self.send_result(oprot, api, result, seqid)


from .tracker import TrackerBase, ConsoleTracker  # noqa
