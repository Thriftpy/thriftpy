# -*- coding: utf-8 -*-

import thriftpy
thriftpy.install_import_hook()

from thriftpy.utils import serialize, deserialize
from thriftpy.protocol import TCyBinaryProtocolFactory

import container_thrift as container


def test_list_item():
    l_item = container.ListItem()
    l_item.list_string = ['foo', 'bar']
    l_item.list_list_string = [['foo', 'bar']]

    b = serialize(l_item, TCyBinaryProtocolFactory())
    l_item2 = deserialize(container.ListItem(), b, TCyBinaryProtocolFactory())
    assert l_item == l_item2


def test_map_item():
    m_item = container.MapItem()
    m_item.map_string = {'foo': 'bar'}
    m_item.map_map_string = {'foo': {'hello': 'world'}}

    b = serialize(m_item, TCyBinaryProtocolFactory())
    m_item2 = deserialize(container.MapItem(), b, TCyBinaryProtocolFactory())
    assert m_item == m_item2


def test_mix_item():
    x_item = container.MixItem()
    x_item.list_map = [{'foo': 'bar'}]
    x_item.map_list = {'foo': ['hello', 'world']}

    b = serialize(x_item, TCyBinaryProtocolFactory())
    x_item2 = deserialize(container.MixItem(), b, TCyBinaryProtocolFactory())
    assert x_item == x_item2


def test_list_struct():
    l_item = container.ListItem()
    l_item.list_string = ['foo', 'bar'] * 100
    l_item.list_list_string = [['foo', 'bar']] * 100

    l_struct = container.ListStruct()
    l_struct.list_items = [l_item] * 100

    b = serialize(l_struct, TCyBinaryProtocolFactory())
    l_struct2 = deserialize(container.ListStruct(), b,
                            TCyBinaryProtocolFactory())
    assert l_struct == l_struct2
