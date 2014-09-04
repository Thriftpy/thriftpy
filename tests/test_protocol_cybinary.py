# -*- coding: utf-8 -*-

import sys
PYPY = "__pypy__" in sys.modules

import pytest
pytestmark = pytest.mark.skipif(PYPY, reason="cybin not enabled in pypy.")

from thriftpy._compat import u
from thriftpy.thrift import TType, TPayload
from thriftpy.transport import TMemoryBuffer, TCyBufferedTransport
from thriftpy.utils import hexlify

if not PYPY:
    from thriftpy.protocol import cybin as proto


class TItem(TPayload):
    thrift_spec = {
        1: (TType.I32, "id"),
        2: (TType.LIST, "phones", (TType.STRING)),
    }
    default_spec = [("id", None), ("phones", None)]


def test_write_bool():
    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    proto.write_val(b, TType.BOOL, 1)
    b.flush()

    assert "01" == hexlify(b.getvalue())


def test_read_bool():
    b = TMemoryBuffer(b'\x01')
    b = TCyBufferedTransport(b)
    val = proto.read_val(b, TType.BOOL)

    assert True is val


def test_write_i8():
    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    proto.write_val(b, TType.I08, 123)
    b.flush()

    assert "7b" == hexlify(b.getvalue())


def test_read_i8():
    b = TMemoryBuffer(b'\x7b')
    b = TCyBufferedTransport(b)
    val = proto.read_val(b, TType.I08)

    assert 123 == val


def test_write_i16():
    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    proto.write_val(b, TType.I16, 12345)
    b.flush()

    assert "30 39" == hexlify(b.getvalue())


def test_read_i16():
    b = TMemoryBuffer(b"09")
    b = TCyBufferedTransport(b)
    val = proto.read_val(b, TType.I16)

    assert 12345 == val


def test_write_i32():
    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    proto.write_val(b, TType.I32, 1234567890)
    b.flush()

    assert "49 96 02 d2" == hexlify(b.getvalue())


def test_read_i32():
    b = TMemoryBuffer(b"I\x96\x02\xd2")
    b = TCyBufferedTransport(b)
    assert 1234567890 == proto.read_val(b, TType.I32)


def test_write_i64():
    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    proto.write_val(b, TType.I64, 1234567890123456789)
    b.flush()
    assert "11 22 10 f4 7d e9 81 15" == hexlify(b.getvalue())


def test_read_i64():
    b = TMemoryBuffer(b"\x11\"\x10\xf4}\xe9\x81\x15")
    b = TCyBufferedTransport(b)
    assert 1234567890123456789 == proto.read_val(b, TType.I64)


def test_write_double():
    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    proto.write_val(b, TType.DOUBLE, 1234567890.1234567890)
    b.flush()
    assert "41 d2 65 80 b4 87 e6 b7" == hexlify(b.getvalue())


def test_read_double():
    b = TMemoryBuffer(b"A\xd2e\x80\xb4\x87\xe6\xb7")
    b = TCyBufferedTransport(b)
    assert 1234567890.1234567890 == proto.read_val(b, TType.DOUBLE)


def test_write_string():
    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    proto.write_val(b, TType.STRING, "hello world!")
    b.flush()
    assert "00 00 00 0c 68 65 6c 6c 6f 20 77 6f 72 6c 64 21" == \
        hexlify(b.getvalue())

    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    proto.write_val(b, TType.STRING, u("你好世界"))
    b.flush()
    assert "00 00 00 0c e4 bd a0 e5 a5 bd e4 b8 96 e7 95 8c" == \
        hexlify(b.getvalue())


def test_read_string():
    b = TMemoryBuffer(b"\x00\x00\x00\x0c"
                      b"\xe4\xbd\xa0\xe5\xa5\xbd\xe4\xb8\x96\xe7\x95\x8c")
    b = TCyBufferedTransport(b)
    assert u("你好世界") == proto.read_val(b, TType.STRING)


def test_write_message_begin():
    b = TMemoryBuffer()
    trans = TCyBufferedTransport(b)
    b = proto.TCyBinaryProtocol(trans)
    b.write_message_begin("test", TType.STRING, 1)
    b.write_message_end()
    assert "80 01 00 0b 00 00 00 04 74 65 73 74 00 00 00 01" == \
        hexlify(trans.getvalue())


def test_read_message_begin():
    b = TMemoryBuffer(b"\x80\x01\x00\x0b\x00\x00\x00\x04test\x00\x00\x00\x01")
    b = TCyBufferedTransport(b)
    res = proto.TCyBinaryProtocol(b).read_message_begin()
    assert res == ("test", TType.STRING, 1)


def test_write_struct():
    b = TMemoryBuffer()
    trans = TCyBufferedTransport(b)
    b = proto.TCyBinaryProtocol(trans)
    item = TItem(id=123, phones=["123456", "abcdef"])
    b.write_struct(item)
    b.write_message_end()
    assert ("08 00 01 00 00 00 7b 0f 00 02 0b 00 00 00 02 00 00 00 "
            "06 31 32 33 34 35 36 00 00 00 06 61 62 63 64 65 66 00") == \
        hexlify(trans.getvalue())


def test_read_struct():
    b = TMemoryBuffer(b"\x08\x00\x01\x00\x00\x00{\x0f\x00\x02\x0b\x00\x00\x00"
                      b"\x02\x00\x00\x00\x06123456\x00\x00\x00\x06abcdef\x00")
    b = TCyBufferedTransport(b)
    b = proto.TCyBinaryProtocol(b)
    _item = TItem(id=123, phones=["123456", "abcdef"])
    _item2 = TItem()
    b.read_struct(_item2)
    assert _item == _item2


def test_write_empty_struct():
    b = TMemoryBuffer()
    trans = TCyBufferedTransport(b)
    b = proto.TCyBinaryProtocol(trans)
    item = TItem()
    b.write_struct(item)
    b.write_message_end()
    assert "00" == hexlify(trans.getvalue())


def test_read_empty_struct():
    b = TMemoryBuffer(b"\x00")
    b = TCyBufferedTransport(b)
    b = proto.TCyBinaryProtocol(b)
    _item = TItem()
    _item2 = TItem()
    b.read_struct(_item2)
    assert _item == _item2


def test_write_huge_struct():
    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    b = proto.TCyBinaryProtocol(b)
    item = TItem(id=12345, phones=["1234567890"] * 100000)
    b.write_struct(item)
    b.write_message_end()


def test_read_huge_args():

    class Hello(TPayload):
        thrift_spec = {
            1: (TType.STRING, "name"),
            2: (TType.STRING, "world"),
        }
        default_spec = [("name", None), ("world", None)]

    b = TMemoryBuffer()
    b = TCyBufferedTransport(b)
    item = Hello(name='我' * 326, world='你' * 1365)
    p = proto.TCyBinaryProtocol(b)
    p.write_struct(item)
    p.write_message_end()

    item2 = Hello()
    p.read_struct(item2)
