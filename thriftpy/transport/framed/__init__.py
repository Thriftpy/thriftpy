# -*- coding: utf-8 -*-

from __future__ import absolute_import

import struct
from io import BytesIO

from thriftpy._compat import CYTHON
from .. import TTransportBase, readall
from ..buffered import TBufferedTransport


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

    def getvalue(self):
        return self.__trans.getvalue()


class TFramedTransportFactory(object):
    def get_transport(self, trans):
        return TBufferedTransport(TFramedTransport(trans))


if CYTHON:
    from .cyframed import TCyFramedTransport, TCyFramedTransportFactory  # noqa
