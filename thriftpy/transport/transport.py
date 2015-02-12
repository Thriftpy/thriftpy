# -*- coding: utf-8 -*-

from __future__ import absolute_import

import struct

from io import BytesIO

from ..ttype import TType, TException


def readall(read_fn, sz):
    buff = b''
    have = 0
    while have < sz:
        chunk = read_fn(sz - have)
        have += len(chunk)
        buff += chunk

        if len(chunk) == 0:
            raise TTransportException(TTransportException.END_OF_FILE,
                                      "End of file reading from transport")

    return buff


class TTransportBase(object):
    """Base class for Thrift transport layer."""

    def read(self, sz):
        return readall(self._read, sz)


class TTransportException(TException):
    """Custom Transport Exception class"""

    thrift_spec = {
        1: (TType.STRING, 'message'),
        2: (TType.I32, 'type'),
    }

    UNKNOWN = 0
    NOT_OPEN = 1
    ALREADY_OPEN = 2
    TIMED_OUT = 3
    END_OF_FILE = 4

    def __init__(self, type=UNKNOWN, message=None):
        super(TTransportException, self).__init__()
        self.type = type
        self.message = message


class TMemoryBuffer(TTransportBase):
    """Wraps a BytesIO object as a TTransport."""

    def __init__(self, value=None):
        """value -- a value as the initial value in the BytesIO object.

        If value is set, the transport can be read first.
        """
        self._buffer = BytesIO(value) if value is not None else BytesIO()
        self._pos = 0

    def is_open(self):
        return not self._buffer.closed

    def open(self):
        pass

    def close(self):
        self._buffer.close()

    def read(self, sz):
        return self._read(sz)

    def _read(self, sz):
        orig_pos = self._buffer.tell()
        self._buffer.seek(self._pos)
        res = self._buffer.read(sz)
        self._buffer.seek(orig_pos)
        self._pos += len(res)
        return res

    def write(self, buf):
        self._buffer.write(buf)

    def flush(self):
        pass

    def getvalue(self):
        return self._buffer.getvalue()

    def setvalue(self, value):
        self._buffer = BytesIO(value)
        self._pos = 0


class TBufferedTransport(TTransportBase):
    """Class that wraps another transport and buffers its I/O.

    The implementation uses a (configurable) fixed-size read buffer
    but buffers all writes until a flush is performed.
    """
    DEFAULT_BUFFER = 4096

    def __init__(self, trans, buf_size=DEFAULT_BUFFER):
        self.__trans = trans
        self.__wbuf = BytesIO()
        self.__rbuf = BytesIO(b"")
        self.__buf_size = buf_size

    def is_open(self):
        return self.__trans.is_open()

    def open(self):
        return self.__trans.open()

    def close(self):
        return self.__trans.close()

    def _read(self, sz):
        ret = self.__rbuf.read(sz)
        if len(ret) != 0:
            return ret

        self.__rbuf = BytesIO(self.__trans.read(max(sz, self.__buf_size)))
        return self.__rbuf.read(sz)

    def write(self, buf):
        self.__wbuf.write(buf)

    def flush(self):
        out = self.__wbuf.getvalue()
        # reset wbuf before write/flush to preserve state on underlying failure
        self.__wbuf = BytesIO()
        self.__trans.write(out)
        self.__trans.flush()


class TBufferedTransportFactory(object):
    def get_transport(self, trans):
        return TBufferedTransport(trans)


class TFramedTransport(TTransportBase):
    """Class that wraps another transport and frames its I/O when writing."""
    def __init__(self, trans):
        self.__trans = trans
        self.__rbuf = BytesIO()

    def is_open(self):
        return self.__trans.is_open()

    def open(self):
        return self.__trans.open()

    def close(self):
        return self.__trans.close()

    def read(self, sz):
        # Important: don't attempt to read the next frame if the caller
        # doesn't actually need any data.
        if sz == 0:
            return b''

        ret = self.__rbuf.read(sz)
        if len(ret) != 0:
            return ret

        self.read_frame()
        return self.__rbuf.read(sz)

    def read_frame(self):
        buff = readall(self.__trans.read, 4)
        sz, = struct.unpack('!i', buff)
        frame = readall(self.__trans.read, sz)
        self.__rbuf = BytesIO(frame)

    def write(self, buf):
        wsz = len(buf)
        # N.B.: Doing this string concatenation is WAY cheaper than making
        # two separate calls to the underlying socket object. Socket writes in
        # Python turn out to be REALLY expensive, but it seems to do a pretty
        # good job of managing string buffer operations without excessive
        # copies
        towrite = struct.pack("!i", wsz) + buf
        self.__trans.write(towrite)
        self.__trans.flush()

    def flush(self):
        pass


class TFramedTransportFactory(object):
    def get_transport(self, trans):
        return TBufferedTransport(TFramedTransport(trans))
