# -*- coding: utf-8 -*-

import pytest

import thriftpy
from thriftpy.thrift import parse_spec, TType


def test_obj_equalcheck():
    ab = thriftpy.load("addressbook.thrift")
    ab2 = thriftpy.load("addressbook.thrift")

    assert ab.Person(name="hello") == ab2.Person(name="hello")


def test_cls_equalcheck():
    ab = thriftpy.load("addressbook.thrift")
    ab2 = thriftpy.load("addressbook.thrift")

    assert ab.Person == ab2.Person


def test_isinstancecheck():
    ab = thriftpy.load("addressbook.thrift")
    ab2 = thriftpy.load("addressbook.thrift")

    assert isinstance(ab.Person(), ab2.Person)
    assert isinstance(ab.Person(name="hello"), ab2.Person)

    assert isinstance(ab.PersonNotExistsError(), ab2.PersonNotExistsError)


def test_unhashable():
    ab = thriftpy.load("addressbook.thrift")

    with pytest.raises(TypeError):
        hash(ab.Person(name="Tom"))


def test_default_value():
    ab = thriftpy.load("addressbook.thrift")

    assert ab.PhoneNumber().type == ab.PhoneType.MOBILE


def test_parse_spec():
    ab = thriftpy.load("addressbook.thrift")

    cases = [
        ((TType.I32, None), "I32"),
        ((TType.STRUCT, ab.PhoneNumber), "PhoneNumber"),
        ((TType.LIST, TType.I32), "LIST<I32>"),
        ((TType.LIST, (TType.STRUCT, ab.PhoneNumber)), "LIST<PhoneNumber>"),
        ((TType.MAP, (TType.STRING, (
            TType.LIST, (TType.MAP, (TType.STRING, TType.STRING))))),
         "MAP<STRING, LIST<MAP<STRING, STRING>>>")
    ]

    for spec, res in cases:
        assert parse_spec(*spec) == res
