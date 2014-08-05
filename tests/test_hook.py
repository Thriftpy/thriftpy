# -*- coding: utf-8 -*-

import pickle
import sys

import pytest

import thriftpy


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
