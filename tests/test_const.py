# -*- coding: utf-8 -*-

from nose.tools import (
    assert_equal,
    assert_list_equal
)

import thriftpy
thriftpy.install_import_hook()

import const_thrift as const


def test_num_const():
    assert_equal(10, const.I16_CONST)
    assert_equal(100000, const.I32_CONST)
    assert_equal(123.456, const.DOUBLE_CONST)


def test_string_const():
    assert_equal("hello", const.DOUBLE_QUOTED_CONST)
    assert_equal("hello", const.SINGLE_QUOTED_CONST)


def test_list_const():
    assert_list_equal([1, 2, 3], const.I32_LIST_CONST)
    assert_list_equal([1.1, 2.2, 3.3], const.DOUBLE_LIST_CONST)
    assert_list_equal(["hello", "world"], const.STRING_LIST_CONST)

    assert_list_equal([[1, 2, 3], [4, 5, 6]], const.I32_LIST_LIST_CONST)
    assert_list_equal([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6]],
                      const.DOUBLE_LIST_LIST_CONST)
    assert_list_equal([["hello", "world"], ["foo", "bar"]],
                      const.STRING_LIST_LIST_CONST)
