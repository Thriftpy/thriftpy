# -*- coding: utf-8 -*-

from thriftpy.utils import serialize, deserialize

import container_thrift as container


def test_list_item():
    l_item = container.ListItem()
    l_item.list_string = ['foo', 'bar']
    l_item.list_list_string = [['foo', 'bar']]

    b = serialize(l_item)
    l_item2 = deserialize(container.ListItem(), b)
    assert l_item == l_item2


def test_map_item():
    m_item = container.MapItem()
    m_item.map_string = {'foo': 'bar'}
    m_item.map_map_string = {'foo': {'hello': 'world'}}

    m_item2 = deserialize(container.MapItem(), serialize(m_item))
    assert m_item == m_item2


def test_mix_item():
    x_item = container.MixItem()
    x_item.list_map = [{'foo': 'bar'}]
    x_item.map_list = {'foo': ['hello', 'world']}

    x_item2 = deserialize(container.MixItem(), serialize(x_item))
    assert x_item == x_item2
