# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
import os

from thriftpy.parser import parse
from thriftpy.parser.exc import ThriftLexerError, ThriftGrammerError


def _json(name):
    path = os.path.join('parser-cases', 'json', name + '.json')
    return json.load(open(path))


def _thrift(name):
    path = os.path.join('parser-cases', 'thrift', name + '.thrift')
    return parse(open(path).read())


class TestParser(object):

    def case(name):
        def _case(self):
            assert _thrift(name) == _json(name)
        return _case

    test_includes = case('includes')
    test_namespaces = case('namespaces')
    test_comments = case('comments')
    test_consts = case('consts')
    test_typedefs = case('typedefs')
    test_enums = case('enums')
    test_unions = case('unions')
    test_structs = case('structs')
    test_exceptions = case('exceptions')
    test_serices = case('services')
    test_tutorial = case('tutorial')
    test_escape = case('escape')

    def test_lexer_exc(self):
        try:
            _thrift('bad_lexer')
        except SyntaxError as e:
            assert isinstance(e, ThriftLexerError)

    def test_lexer_bad_escaping_exc(self):
        try:
            _thrift('bad_lexer_escaping')
        except SyntaxError as e:
            assert isinstance(e, ThriftLexerError)

    def test_bad_grammer(self):
        try:
            _thrift('bad_grammer')
        except SyntaxError as e:
            assert isinstance(e, ThriftGrammerError)
