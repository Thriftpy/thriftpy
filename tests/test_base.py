# -*- coding: utf-8 -*-

import thriftpy


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


def test_hashable():
    ab = thriftpy.load("addressbook.thrift")

    hash(ab.Person(name="Tom"))


def test_default_value():
    ab = thriftpy.load("addressbook.thrift")

    assert ab.PhoneNumber().type == ab.PhoneType.MOBILE
