# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .binary import TBinaryProtocol, TBinaryProtocolFactory
from .json import TJSONProtocol, TJSONProtocolFactory

from thriftpy._compat import PYPY
if not PYPY:
    from .cybin import TCyBinaryProtocol, TCyBinaryProtocolFactory
else:
    TCyBinaryProtocol = TBinaryProtocol
    TCyBinaryProtocolFactory = TBinaryProtocolFactory

__all__ = ['TBinaryProtocol', 'TBinaryProtocolFactory',
           'TCyBinaryProtocol', 'TCyBinaryProtocolFactory',
           'TJSONProtocol', 'TJSONProtocolFactory']
