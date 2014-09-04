# -*- coding: utf-8 -*-

from __future__ import absolute_import


class ThriftSyntaxError(SyntaxError):
    pass


class ThriftLexerError(ThriftSyntaxError):
    pass


class ThriftGrammerError(ThriftSyntaxError):
    pass
