# -*- coding: utf-8 -*-

"""
    thriftpy.thrift
    ~~~~~~~~~~~~~~~~~~

    Thrift simplified.
"""

from __future__ import absolute_import

import functools
import time

import thriftpy.trace as trace
from .ttype import TMessageType, TType, TApplicationException


def args2kwargs(thrift_spec, *args):
    arg_names = [item[1][1] for item in sorted(thrift_spec.items())]
    return dict(zip(arg_names, args))


class TClient(object):
    def __init__(self, service, iprot, oprot=None):
        self._service = service
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def __getattr__(self, _api):
        if _api in self._service.thrift_services:
            return functools.partial(self._req, _api)

        raise AttributeError("{} instance has no attribute '{}'".format(
            self.__class__.__name__, _api))

    def __dir__(self):
        return self._service.thrift_services

    def _req(self, _api, *args, **kwargs):
        _kw = args2kwargs(getattr(self._service, _api + "_args").thrift_spec,
                          *args)
        kwargs.update(_kw)
        result_cls = getattr(self._service, _api + "_result")

        self._send(_api, **kwargs)
        # wait result only if non-oneway
        if not getattr(result_cls, "oneway"):
            return self._recv(_api)

    def _send(self, _api, **kwargs):
        self._oprot.write_message_begin(_api, TMessageType.CALL, self._seqid)
        args = getattr(self._service, _api + "_args")()
        for k, v in kwargs.items():
            setattr(args, k, v)
        args.write(self._oprot)
        self._oprot.write_message_end()
        self._oprot.trans.flush()

    def _recv(self, _api):
        fname, mtype, rseqid = self._iprot.read_message_begin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(self._iprot)
            self._iprot.read_message_end()
            raise x
        result = getattr(self._service, _api + "_result")()
        result.read(self._iprot)
        self._iprot.read_message_end()

        if hasattr(result, "success") and result.success is not None:
            return result.success

        # void api without throws
        if len(result.thrift_spec) == 0:
            return

        # check throws
        for k, v in result.__dict__.items():
            if k != "success" and v is not None:
                raise v

        # no throws & not void api
        if hasattr(result, "success"):
            raise TApplicationException(TApplicationException.MISSING_RESULT)


class TProcessor(object):
    """Base class for procsessor, which works on two streams."""

    def __init__(self, service, handler):
        self._service = service
        self._handler = handler

    def process_in(self, iprot):
        api, _, seqid = iprot.read_message_begin()
        result, call = self._process_in(api, iprot)
        return api, seqid, result, call

    def _process_in(self, api, iprot):
        if api not in self._service.thrift_services:
            iprot.skip(TType.STRUCT)
            iprot.read_message_end()
            return TApplicationException(TApplicationException.UNKNOWN_METHOD), None   # noqa
        else:
            args = getattr(self._service, api + "_args")()
            args.read(iprot)
            iprot.read_message_end()
            result = getattr(self._service, api + "_result")()

            # convert kwargs to args
            api_args = [args.thrift_spec[k][1]
                        for k in sorted(args.thrift_spec)]
            call = lambda: getattr(self._handler, api)(
                *(args.__dict__[k] for k in api_args)
            )
            return result, call

    def send_exception(self, oprot, api, exc, seqid):
        oprot.write_message_begin(api, TMessageType.EXCEPTION, seqid)
        exc.write(oprot)
        oprot.write_message_end()
        oprot.trans.flush()

    def send_result(self, oprot, api, result, seqid):
        oprot.write_message_begin(api, TMessageType.REPLY, seqid)
        result.write(oprot)
        oprot.write_message_end()
        oprot.trans.flush()

    def handle_exception(self, e, result):
        for k in sorted(result.thrift_spec):
            if result.thrift_spec[k][1] == "success":
                continue

            _, exc_name, exc_cls, _ = result.thrift_spec[k]
            if isinstance(e, exc_cls):
                setattr(result, exc_name, e)
                break
        else:
            raise

    def process(self, iprot, oprot):
        res = self.process_in(iprot)
        self._do_process(iprot, oprot, *res)

    def _do_process(self, iprot, oprot, api, seqid, result, call):
        if isinstance(result, TApplicationException):
            self.send_exception(oprot, api, result, seqid)
        else:
            try:
                result.success = call()
            except Exception as e:
                # raise if api don't have throws
                self.handle_exception(e, result)

            if not result.oneway:
                self.send_result(oprot, api, result, seqid)


class TTrackedClient(TClient):
    def __init__(self, track_handler, *args, **kwargs):
        super(TTrackedClient, self).__init__(*args, **kwargs)

        self.track_handler = track_handler
        self._upgraded = False

        try:
            self._negotiation()
            self._upgraded = True
        except TApplicationException as e:
            if e.type != TApplicationException.UNKNOWN_METHOD:
                raise

    def _negotiation(self):
        self._oprot.write_message_begin(trace.method_name, TMessageType.CALL,
                                        self._seqid)
        args = trace.thrift.UpgradeArgs()
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
            result = trace.thrift.UpgradeReply()
            result.read(self._iprot)
            self._iprot.read_message_end()

    def _req(self, *args, **kwargs):
        if not self._upgraded:
            return super(TTrackedClient, self)._req(*args, **kwargs)

        exception = None
        try:
            res = super(TTrackedClient, self)._req(*args, **kwargs)
            self._header.status = True
            return res
        except Exception as e:
            exception = e
            self._header.status = False
            raise
        finally:
            self._header.end = int(time.time() * 1000)
            self.track_handler.record(self._header, exception)

    def _send(self, _api, **kwargs):
        if self._upgraded:
            self._header = trace.thrift.RequestHeader(api=_api)
            self.track_handler.gen_header(self._header)
            self._header.write(self._oprot)

        super(TTrackedClient, self)._send(_api, **kwargs)


class TTrackedProcessor(TProcessor):
    def __init__(self, track_handler, *args, **kwargs):
        super(TTrackedProcessor, self).__init__(*args, **kwargs)

        self.track_handler = track_handler
        self._upgraded = False

    def _try_upgrade(self, iprot):
        api, msg_type, seqid = iprot.read_message_begin()
        if msg_type == TMessageType.CALL and api == trace.method_name:
            self._upgraded = True

            args = trace.thrift.UpgradeArgs()
            args.read(iprot)
            result = trace.thrift.UpgradeReply()
            result.oneway = False
            call = lambda: None
            iprot.read_message_end()
        else:
            result, call = self._process_in(api, iprot)

        return api, seqid, result, call

    def process(self, iprot, oprot):
        if not self._upgraded:
            res = self._try_upgrade(iprot)
        else:
            request_header = trace.thrift.RequestHeader()
            request_header.read(iprot)
            self.track_handler.handle(request_header)
            res = super(TTrackedProcessor, self).process_in(iprot)

        self._do_process(iprot, oprot, *res)


class TProcessorFactory(object):
    def __init__(self, service, handler, tracker_handler=None,
                 processor_class=None):
        self.service = service
        self.handler = handler
        self.tracker_handler = tracker_handler
        self.processor_class = processor_class or TProcessor

    def get_processor(self):
        args = [self.service, self.handler]
        if self.tracker_handler:
            args.insert(0, self.tracker_handler)

        return self.processor_class(*args)


# backward compat
from .ttype import TPayloadMeta, gen_init, TPayload, TException  # noqa
