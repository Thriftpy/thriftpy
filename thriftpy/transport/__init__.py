# -*- coding: utf-8 -*-

from __future__ import absolute_import

__all__ = [
    'TSocketBase', 'TSocket', 'TServerSocket',
    'TTransportBase', 'TTransportException',
    'TMemoryBuffer',
    'TFramedTransport', 'TFramedTransportFactory',
    'TBufferedTransport', 'TBufferedTransportFactory',
    'TCyBufferedTransport', 'TCyBufferedTransportFactory',
]


from .socket import TSocketBase, TSocket, TServerSocket
from .transport import (
    TTransportBase,
    TTransportException,
    TMemoryBuffer,
    TFramedTransport,
    TFramedTransportFactory,
)

from thriftpy._compat import PYPY
if PYPY:
    from .transport import TBufferedTransport, TBufferedTransportFactory
else:
    from .cytransport import TBufferedTransport, TBufferedTransportFactory

# backward compatible
TCyBufferedTransport = TBufferedTransport
TCyBufferedTransportFactory = TBufferedTransportFactory
