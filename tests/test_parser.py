# -*- coding: utf-8 -*-


import os
import sys
import json

from thriftpy import parse


def _json(name):
    path = os.path.join('parser-cases', 'json', name + '.json')
    return json.load(open(path))


def _thrift(name):
    path = os.path.join('parser-cases', 'thrift', name + '.thrift')
    dct = parse(open(path).read())
    return dct


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
