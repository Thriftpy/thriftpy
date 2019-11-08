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
        self._buffer = BytesIO(value) if value is not None else BytesIO()

    def is_open(self):
        return not self._buffer.closed

    def open(self):
        pass

    def close(self):
        self._buffer.close()

    def read(self, sz):
        return self._buffer.read(sz)

    def write(self, buf):
        origin_pos = self._buffer.tell()
        self._buffer.seek(0, 2)
        self._buffer.write(buf)
        self._buffer.seek(origin_pos)

    def flush(self):
        pass

    def getvalue(self):
        pos = self._buffer.tell()
        return self._buffer.getvalue()[pos:]

    def setvalue(self, value):
        self._buffer = BytesIO(value)

    def clean(self):
        self._buffer.seek(0, 0)
        self._buffer.truncate(0)


if CYTHON:
    from .cymemory import TCyMemoryBuffer  # noqa
