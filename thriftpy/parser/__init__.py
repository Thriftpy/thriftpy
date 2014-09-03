# -*- coding: utf-8 -*-
# flake8: noqa

"""
    thriftpy.parser
    ~~~~~~~~~~~~~~~

    thrift parser using ply
"""


class ThriftSyntaxError(SyntaxError):
    pass


class ThriftLexerError(ThriftSyntaxError):
    pass


class ThriftGrammerError(ThriftSyntaxError):
    pass


from .parser import parse
