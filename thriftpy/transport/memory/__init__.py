# -*- coding: utf-8 -*-

from __future__ import absolute_import

from io import BytesIO

from thriftpy._compat import CYTHON
from .. import TTransportBase


class TMemoryBuffer(TTransportBase):
    """Wraps a BytesIO object as a TTransport."""

    def __init__(self, value=None):
        """value -- a value as the initial value in the BytesIO object.

        If value is set, the transport can be read first.
        """
        self.value = value
        self.open()

    def is_open(self):
        return not self._buffer.closed

    def open(self):
        if self.value is not None:
            buf = BytesIO(self.value)
        else:
            buf = BytesIO()
        self._buffer = buf
        self._pos = 0

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


if CYTHON:
    from .cymemory import TCyMemoryBuffer  # noqa
