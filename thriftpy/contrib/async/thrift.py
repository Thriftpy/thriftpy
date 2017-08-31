# -*- coding: utf-8 -*-
from __future__ import absolute_import

import asyncio

from thriftpy.thrift import (
    TType,
    TMessageType,
    TApplicationException,
    init_func_generator
)

from thriftpy._compat import with_metaclass


class TProcessor(object):
    """Base class for procsessor, which works on two streams."""

    def __init__(self, service, handler):
        self._service = service
        self._handler = handler

    def process_in(self, iprot):
        api, type, seqid = iprot.read_message_begin()
        if api not in self._service.thrift_services:
            iprot.skip(TType.STRUCT)
            iprot.read_message_end()
            return api, seqid, TApplicationException(TApplicationException.UNKNOWN_METHOD), None  # noqa

        args = getattr(self._service, api + "_args")()
        args.read(iprot)
        iprot.read_message_end()
        result = getattr(self._service, api + "_result")()

        # convert kwargs to args
        api_args = [args.thrift_spec[k][1] for k in sorted(args.thrift_spec)]

        def call():
            f = getattr(self._handler, api)
            return f(*(args.__dict__[k] for k in api_args))

        return api, seqid, result, call

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
        api, seqid, result, call = self.process_in(iprot)

        if isinstance(result, TApplicationException):
            return self.send_exception(oprot, api, result, seqid)

        try:
            result.success = call()
        except Exception as e:
            # raise if api don't have throws
            self.handle_exception(e, result)

        if not result.oneway:
            self.send_result(oprot, api, result, seqid)


class TPayloadMeta(type):

    def __new__(cls, name, bases, attrs):
        if "default_spec" in attrs:
            spec = attrs.pop("default_spec")
            attrs["__init__"] = init_func_generator(cls, spec)
        return super(TPayloadMeta, cls).__new__(cls, name, bases, attrs)


class TPayload(with_metaclass(TPayloadMeta, object)):

    __hash__ = None

    @asyncio.coroutine
    def read(self, iprot):
        yield from iprot.read_struct(self)

    @asyncio.coroutine
    def write(self, oprot):
        yield from oprot.write_struct(self)

    def __repr__(self):
        l = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(l))

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)
