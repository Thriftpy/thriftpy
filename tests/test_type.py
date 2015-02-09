# -*- coding: utf-8 -*-

from thriftpy import load
from thriftpy.thrift import TType


def test_set():
    s = load("type.thrift")

    assert s.Set.thrift_spec == {1: (TType.SET, "a_set", TType.STRING, True)}
