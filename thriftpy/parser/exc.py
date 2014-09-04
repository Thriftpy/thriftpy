# -*- coding: utf-8 -*-


class ThriftSyntaxError(SyntaxError):
    pass


class ThriftLexerError(ThriftSyntaxError):
    pass


class ThriftGrammerError(ThriftSyntaxError):
    pass
