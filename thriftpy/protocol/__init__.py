# -*- coding: utf-8 -*-

from __future__ import absolute_import

__all__ = ['TBinaryProtocol', 'TBinaryProtocolFactory',
           'TCyBinaryProtocol', 'TCyBinaryProtocolFactory',
           'TJSONProtocol', 'TJSONProtocolFactory']


from .json import TJSONProtocol, TJSONProtocolFactory

from thriftpy._compat import PYPY
if PYPY:
    from .binary import TBinaryProtocol, TBinaryProtocolFactory
else:
    from .cybin import TBinaryProtocol, TBinaryProtocolFactory

# backward compatible
TCyBinaryProtocol = TBinaryProtocol
TCyBinaryProtocolFactory = TBinaryProtocolFactory
