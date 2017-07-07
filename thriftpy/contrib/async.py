from thriftpy.thrift import TType, TMessageType, TApplicationException, TProcessor, TClient, args2kwargs
from thriftpy.transport import TMemoryBuffer
from thriftpy.protocol import TBinaryProtocolFactory

import asyncio
import struct

import logging
LOG = logging.getLogger(__name__)


class TAsyncTransport(TMemoryBuffer):
    def __init__(self, trans):
        super().__init__()
        self._trans = trans
        self._io_lock = asyncio.Lock()

    def flush(self):
        buf = self.getvalue()
        self._trans.write(struct.pack("!i", len(buf)) + buf)
        self.setvalue(b'')

    @asyncio.coroutine
    def read_frame(self):
        # do not yield the event loop on a single reader
        # between reading the frame_size and the buffer
        with (yield from self._io_lock):
            buff = yield from self._trans.readexactly(4)
            sz, = struct.unpack('!i', buff)

            frame = yield from self._trans.readexactly(sz)
            self.setvalue(frame)

    @asyncio.coroutine
    def drain(self):
        # drain cannot be called concurrently
        with (yield from self._io_lock):
            yield from self._trans.drain()


class TAsyncReader(TAsyncTransport):
    def close(self):
        self._trans.feed_eof()
        super().close()


class TAsyncWriter(TAsyncTransport):
    def close(self):
        self._trans.write_eof()
        super().close()


class TAsyncProcessor(TProcessor):
    def __init__(self, service, handler):
        self._service = service
        self._handler = handler

    @asyncio.coroutine
    def process(self, iprot, oprot):
        # the standard thrift protocol packs a single request per frame
        # note that chunked requests are not supported, and would require
        # additional sequence information
        yield from iprot.trans.read_frame()
        api, seqid, result, call = self.process_in(iprot)

        if isinstance(result, TApplicationException):
            self.send_exception(oprot, api, result, seqid)
            yield from oprot.trans.drain()

        try:
            result.success = yield from call()
        except Exception as e:
            # raise if api don't have throws
            self.handle_exception(e, result)

        if not result.oneway:
            self.send_result(oprot, api, result, seqid)
            yield from oprot.trans.drain()


class TAsyncServer(object):
    def __init__(self, processor,
                 iprot_factory=None,
                 oprot_factory=None,
                 timeout=None):
        self.processor = processor
        self.iprot_factory = iprot_factory or TBinaryProtocolFactory()
        self.oprot_factory = oprot_factory or self.iprot_factory
        self.timeout = timeout

    @asyncio.coroutine
    def __call__(self, reader, writer):
        itrans = TAsyncReader(reader)
        iproto = self.iprot_factory.get_protocol(itrans)

        otrans = TAsyncWriter(writer)
        oproto = self.oprot_factory.get_protocol(otrans)

        while not reader.at_eof():
            try:
                fut = self.processor.process(iproto, oproto)
                yield from asyncio.wait_for(fut, self.timeout)
            except ConnectionError:
                LOG.debug('client has closed the connection')
                writer.close()
            except asyncio.TimeoutError:
                LOG.debug('timeout when processing the client request')
                writer.close()
            except asyncio.IncompleteReadError:
                LOG.debug('client has closed the connection')
                writer.close()
            except Exception:
                # app exception
                LOG.exception('unhandled app exception')
                writer.close()
        writer.close()


class TAsyncClient(TClient):
    def __init__(self, *args, timeout=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = timeout

    @asyncio.coroutine
    def _req(self, _api, *args, **kwargs):
        fut = self._req_impl(_api, *args, **kwargs)
        result = yield from asyncio.wait_for(fut, self.timeout)
        return result

    @asyncio.coroutine
    def _req_impl(self, _api, *args, **kwargs):
        args_cls = getattr(self._service, _api + "_args")
        _kw = args2kwargs(args_cls.thrift_spec, *args)

        kwargs.update(_kw)
        result_cls = getattr(self._service, _api + "_result")

        self._send(_api, **kwargs)
        yield from self._oprot.trans.drain()

        # wait result only if non-oneway
        if not getattr(result_cls, "oneway"):
            yield from self._iprot.trans.read_frame()
            return self._recv(_api)

    def close(self):
        self._iprot.trans.close()
        self._oprot.trans.close()


@asyncio.coroutine
def make_server(
        service,
        handler,
        host = 'localhost',
        port = 9090,
        proto_factory = TBinaryProtocolFactory(),
        loop = None,
        timeout = None
    ):
    """
    create a thrift server running on an asyncio event-loop.
    """
    processor = TAsyncProcessor(service, handler)
    if loop is None:
        loop = asyncio.get_event_loop()
    server = yield from asyncio.start_server(
        TAsyncServer(processor, proto_factory, timeout=timeout), host, port, loop=loop)
    return server


@asyncio.coroutine
def make_client(service,
                host = 'localhost',
                port = 9090,
                proto_factory = TBinaryProtocolFactory(),
                timeout = None,
                loop = None):
    if loop is None:
        loop = asyncio.get_event_loop()

    reader, writer = yield from asyncio.open_connection(
        host, port, loop=loop)

    itrans = TAsyncReader(reader)
    iproto = proto_factory.get_protocol(itrans)

    otrans = TAsyncWriter(writer)
    oproto = proto_factory.get_protocol(otrans)
    return TAsyncClient(service, iproto, oproto)
