# -*- coding: utf-8 -*-
import pytest

from thriftpy.protocol import TJSONProtocol
from thriftpy.thrift import BINARY, TPayload, TType
from thriftpy.transport import TMemoryBuffer
from thriftpy._compat import u

import thriftpy.protocol.json as proto


class TItem(TPayload):
    thrift_spec = {
        1: (TType.I32, "id", False),
        2: (TType.LIST, "phones", TType.STRING, False),
        3: (TType.STRING, "binary", BINARY, False),
    }
    default_spec = [("id", None), ("phones", None), ("binary", None)]


def test_map_to_obj():
    val = [{"key": "ratio", "value": "0.618"}]
    spec = [TType.STRING, TType.DOUBLE]
    obj = proto.map_to_obj(val, spec)

    assert {"ratio": 0.618} == obj


def test_map_to_json():
    obj = {"ratio": 0.618}
    spec = [TType.STRING, TType.DOUBLE]
    json = proto.map_to_json(obj, spec)

    assert [{"key": "ratio", "value": 0.618}] == json


def test_list_to_obj():
    val = [4, 8, 4, 12, 67]
    spec = TType.I32
    obj = proto.list_to_obj(val, spec)

    assert [4, 8, 4, 12, 67] == obj


def test_list_to_json():
    val = [4, 8, 4, 12, 67]
    spec = TType.I32
    json = proto.list_to_json(val, spec)

    assert [4, 8, 4, 12, 67] == json


def test_struct_to_json():
    obj = TItem(id=13, phones=["5234", "12346456"], binary=b"\xff")
    json = proto.struct_to_json(obj)

    assert {"id": 13, "phones": ["5234", "12346456"], "binary": "/w=="} == json


# We need to support base64 payloads with and without padding, hence two
# variants
@pytest.mark.parametrize("encoded_binary", ["/w==", "/w"])
def test_struct_to_obj(encoded_binary):
    json = {"id": 13, "phones": ["5234", "12346456"], "binary": encoded_binary}
    obj = TItem()

    obj = proto.struct_to_obj(json, obj)

    assert obj.id == 13 and obj.phones == ["5234", "12346456"] and \
        obj.binary == b"\xff"


def test_json_proto_api_write():
    obj = TItem(id=13, phones=["5234", "12346456"], binary=b"\xff")
    trans = TMemoryBuffer()

    p = TJSONProtocol(trans)
    p.write_struct(obj)

    data = trans.getvalue().decode("utf-8")
    length = data[0:4]

    import json
    data = json.loads(data[4:])

    assert length == "\x00\x00\x00e" and data == {
        "metadata": {"version": 1},
        "payload": {"phones": ["5234", "12346456"], "id": 13,
                    "binary": "/w=="}}


def test_json_proto_api_read():
    obj = TItem(id=13, phones=["5234", "12346456"], binary=b"\xff")
    trans = TMemoryBuffer()

    p = TJSONProtocol(trans)
    p.write_struct(obj)

    obj2 = TItem()
    obj2 = p.read_struct(obj2)

    assert obj.id == 13 and obj.phones == ["5234", "12346456"]


def test_unicode_string():
    class Foo(TPayload):
        thrift_spec = {
            1: (TType.STRING, "name", False)
        }
        default_spec = [("name", None)]

    trans = TMemoryBuffer()
    p = TJSONProtocol(trans)

    foo = Foo(name=u('pão de açúcar'))
    foo.write(p)

    foo2 = Foo()
    foo2.read(p)

    assert foo == foo2
