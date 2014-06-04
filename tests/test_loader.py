# -*- coding: utf-8 -*-

from nose.tools import (
    assert_dict_equal,
    assert_equal,
    assert_list_equal,
    assert_true,
)

import thriftpy  # noqa
from thriftpy.thrift import TPayload, TException

import addressbook as ab
import addressbook_thrift as ab_tt


def test_load_const():
    assert_equal(ab.DEFAULT_LIST_SIZE, ab_tt.DEFAULT_LIST_SIZE)


def test_load_enum():
    assert_equal(ab.PhoneType.MOBILE, ab_tt.PhoneType.MOBILE)
    assert_equal(ab.PhoneType.HOME, ab_tt.PhoneType.HOME)
    assert_equal(ab.PhoneType.WORK, ab_tt.PhoneType.WORK)


def test_load_struct():
    assert_equal(ab_tt.PhoneNumber.__base__, TPayload)
    assert_dict_equal(ab.PhoneNumber.thrift_spec,
                      ab_tt.PhoneNumber.thrift_spec)

    # TODO make this work
    # assert_equal(ab_tt.Person.__base__, TPayload)
    # assert_dict_equal(ab.Person.thrift_spec, ab_tt.Person.thrift_spec)

    # assert_true(ab_tt.AddressBook.__base__, TPayload)
    # assert_dict_equal(ab.AddressBook.thrift_spec,
    #                   ab_tt.AddressBook.thrift_spec)


def test_load_exc():
    assert_true(ab_tt.PersonNotExistsError.__base__, TException)
    assert_dict_equal(ab.PersonNotExistsError.thrift_spec,
                      ab_tt.PersonNotExistsError.thrift_spec)


def test_load_service():
    assert_list_equal(ab.AddressBookService.thrift_services,
                      ab_tt.AddressBookService.thrift_services)
