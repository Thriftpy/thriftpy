# -*- coding: utf-8 -*-

from __future__ import absolute_import

from io import BytesIO

from thriftpy._compat import CYTHON
from .. import TTransportBase


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

    def getvalue(self):
        return self.__trans.getvalue()


class TBufferedTransportFactory(object):
    def get_transport(self, trans):
        return TBufferedTransport(trans)


if CYTHON:
    from .cybuffered import TCyBufferedTransport, TCyBufferedTransportFactory  # noqa
