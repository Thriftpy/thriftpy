# -*- coding: utf-8 -*-

from __future__ import absolute_import

import pickle
import sys

import pytest

import thriftpy

PICKLED_BYTES = b"\x80\x02caddressbook_thrift\nPerson\nq\x00)\x81q\x01}q\x02(X\x04\x00\x00\x00nameq\x03X\x03\x00\x00\x00Bobq\x04X\x06\x00\x00\x00phonesq\x05NX\n\x00\x00\x00created_atq\x06Nub."  # noqa


def test_import_hook():
    ab_1 = thriftpy.load("addressbook.thrift")
    print("Load file succeed.")
    assert ab_1.DEFAULT_LIST_SIZE == 10

    try:
        import addressbook_thrift as ab  # noqa
    except ImportError:
        print("Import hook not installed.")

    thriftpy.install_import_hook()

    import addressbook_thrift as ab_2
    print("Magic import succeed.")
    assert ab_2.DEFAULT_LIST_SIZE == 10


def test_load():
    ab_1 = thriftpy.load("addressbook.thrift")
    ab_2 = thriftpy.load("addressbook.thrift",
                         module_name="addressbook_thrift")

    assert ab_1.__name__ == "addressbook"
    assert ab_2.__name__ == "addressbook_thrift"

    # load without module_name can't do pickle
    with pytest.raises(pickle.PicklingError):
        pickle.dumps(ab_1.Person(name='Bob'))

    # load with module_name set and it can be pickled
    person = ab_2.Person(name='Bob')
    assert person == pickle.loads(pickle.dumps(person))


def test_load_module():
    ab = thriftpy.load_module("addressbook_thrift")
    assert ab.__name__ == "addressbook_thrift"
    assert sys.modules["addressbook_thrift"] == ab

    # note we can import after load_module
    import addressbook_thrift as ab2
    assert ab2 == ab


def test_duplicate_loads():
    # multiple loads with same module_name returns the same module
    ab_1 = thriftpy.load("addressbook.thrift",
                         module_name="addressbook_thrift")
    ab_2 = thriftpy.load("./addressbook.thrift",
                         module_name="addressbook_thrift")
    assert ab_1 == ab_2


def test_tpayload_pickle():
    ab = thriftpy.load_module("addressbook_thrift")

    person = ab.Person(name="Bob")
    person_2 = pickle.loads(PICKLED_BYTES)

    assert person == person_2


def test_load_slots():
    thrift = thriftpy.load(
        'addressbook.thrift',
        use_slots=True,
        module_name='addressbook_thrift'
    )

    # normal structs will have slots
    assert thrift.PhoneNumber.__slots__ == ['type', 'number', 'mix_item']
    assert thrift.Person.__slots__ == ['name', 'phones', 'created_at']
    assert thrift.AddressBook.__slots__ == ['people']

    # get/set undefined attributes
    person = thrift.Person()
    with pytest.raises(AttributeError):
        person.attr_not_exist = "Does not work"

    with pytest.raises(AttributeError):
        person.attr_not_exist

    pn = thrift.PhoneNumber()
    with pytest.raises(AttributeError):
        pn.attr_not_exist = "Does not work"

    with pytest.raises(AttributeError):
        pn.attr_not_exist

    ab = thrift.AddressBook()
    with pytest.raises(AttributeError):
        ab.attr_not_exist = "Does not work"

    with pytest.raises(AttributeError):
        ab.attr_not_exist
    # eo: get/set

    # exceptions will not have slots
    assert not hasattr(thrift.PersonNotExistsError, '__slots__')

    # enums will not have slots
    assert not hasattr(thrift.PhoneType, '__slots__')

    # service itself will not be created with slots
    assert not hasattr(thrift.AddressBookService, '__slots__')

    # service args will have slots
    args_slots = thrift.AddressBookService.get_phonenumbers_args.__slots__
    assert args_slots == ['name', 'count']

    result_slots = thrift.AddressBookService.get_phonenumbers_result.__slots__
    assert result_slots == ['success']

    # should be able to pickle slotted objects - if load with module_name
    bob = thrift.Person(name="Bob")
    p_str = pickle.dumps(bob)

    assert pickle.loads(p_str) == bob

    # works for recursive types too
    rec = thriftpy.load('parser-cases/recursive_union.thrift', use_slots=True)
    rec_slots = rec.Dynamic.__slots__
    assert rec_slots == ['boolean', 'integer', 'doubl', 'str', 'arr', 'object']
    dyn = rec.Dynamic()
    with pytest.raises(AttributeError):
        dyn.attr_not_exist = "shouldn't work"
