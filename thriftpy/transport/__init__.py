# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .socket import TSocketBase, TSocket, TServerSocket
from .transport import (
    TTransportBase,
    TTransportException,
    TMemoryBuffer,
    TBufferedTransport,
    TBufferedTransportFactory,
    TFramedTransport,
    TFramedTransportFactory,
)

from thriftpy._compat import PYPY, CYTHON
if not PYPY:
    # enable cython binary by default for CPython.
    if CYTHON:
        from .cytransport import (
            TCyBufferedTransport,
            TCyBufferedTransportFactory,
            TCyFramedTransportFactory,
        )
        TBufferedTransport = TCyBufferedTransport  # noqa
        TBufferedTransportFactory = TCyBufferedTransportFactory  # noqa
        TFramedTransportFactory = TCyFramedTransportFactory  # noqa
else:
    # disable cython binary protocol for PYPY since it's slower.
    TCyBufferedTransport = TBufferedTransport
    TCyBufferedTransportFactory = TBufferedTransportFactory
    TCyFramedTransportFactory = TFramedTransportFactory

__all__ = [
    'TSocketBase', 'TSocket', 'TServerSocket',
    'TTransportBase', 'TTransportException',
    'TMemoryBuffer',
    'TFramedTransport', 'TFramedTransportFactory',
    'TBufferedTransport', 'TBufferedTransportFactory',
    'TCyBufferedTransport', 'TCyBufferedTransportFactory',
    ]
