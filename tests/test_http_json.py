import json
import contextlib
import pytest

from thriftpy.transport import TMemoryBuffer
from thriftpy.thrift import TPayload, TType, TMessageType
from thriftpy.contrib.http import THTTPJsonProtocol, HTTPJsonException
from thriftpy.contrib.http.json_proto import serialize_args, Converter, \
    TProtocolException, httplib


class User(TPayload):
    thrift_spec = {
        1: (TType.STRING, "name", False),
        2: (TType.I32, "id", False)
    }
    default_spec = [('name', None), ("id", None)]


class UserException(TPayload):
    thrift_spec = {
        1: (TType.STRING, "cl", False),
        2: (TType.MAP, "fields", (TType.STRING, TType.STRING), False),
        3: (TType.STRING, "msg", False)
    }
    default_spec = [('cl', None), ("fields", None), ("msg", None)]


class Item(TPayload):
    thrift_spec = {
        1: None
    }
    default_spec = [('a', None)]

    @classmethod
    @contextlib.contextmanager
    def set_spec(cls, ttype, spec=None):
        s = [ttype, 'a', False]
        if spec:
            s.insert(2, spec)

        cls.thrift_spec[1] = tuple(s)

        try:
            yield
        finally:
            cls.thrift_spec[1] = None


@pytest.fixture
def res_struct():
    class _Result(object):
        pass

    class _S(object):
        def __init__(self, spec=None):
            thrift_spec = {
                0: (TType.STRUCT, "success", User, False)
            }
            default_spec = [("success", None)]
            if spec:
                thrift_spec[1] = spec
                default_spec.append((spec[1], None))

            _Result.thrift_spec = thrift_spec
            _Result.default_spec = default_spec
            self.Result = _Result
    return _S


@pytest.fixture
def http_entity():
    class _S(object):
        def __init__(self):
            self.length = 2
            self.payload = {}
            self.line = "HTTP/1.1 200 OK"

            self.headers = [
                "Content-Type: application/json; charset=utf-8",
                "Connection: keep-alive",
            ]

        @property
        def data(self):
            return '\r\n'.join([self.line] + self.headers +
                               ["Content-Length: %d" % self.length, ''] +
                               [json.dumps(self.payload)]).encode("utf-8")
    return _S()


def test_serialize_args_bool():
    with Item.set_spec(TType.BOOL):
        a = serialize_args(Item(True))
    assert {'a': 'true'} == a


def test_serialize_args_i32():
    with Item.set_spec(TType.I32):
        a = serialize_args(Item(123))
    assert {'a': '123'} == a


def test_serialize_args_double():
    with Item.set_spec(TType.DOUBLE):
        a = serialize_args(Item(123.234235))
    assert {'a': '123.234235'} == a


def test_serialize_args_string():
    with Item.set_spec(TType.STRING):
        a = serialize_args(Item("hello"))
    assert {'a': '"hello"'} == a


def test_serialize_args_list():
    with Item.set_spec(TType.LIST, TType.STRING):
        a = serialize_args(Item(["hello", "world"]))
    assert {'a': '["hello", "world"]'} == a


def test_serialize_args_map():
    with Item.set_spec(TType.MAP, (TType.STRING, TType.STRING)):
        a = serialize_args(Item({"hello": "world"}))
    assert {'a': '{"hello": "world"}'} == a


def test_serialize_args_struct():
    with Item.set_spec(TType.STRUCT, User):
        a = serialize_args(Item(User(name="hello", id=123)))
    assert {"name": "hello", "id": 123} == json.loads(a['a'])


def test_map_convert():
    data = {"hello": 123}

    v = Converter.thrift_map(data, (TType.STRING, TType.I32))
    assert v == {"hello": 123}

    v = Converter.json_map(data, (TType.STRING, TType.I32))
    assert v == {"hello": 123}

    data = {("hello", "world"): 0.213}
    with pytest.raises(TProtocolException) as exc:
        Converter.json_map(data, ((TType.SET, TType.STRING), TType.DOUBLE))
    assert "not supported" in str(exc.value)


def test_write_message(http_entity):
    t = TMemoryBuffer()
    p = THTTPJsonProtocol(t)

    user = User(name="hello", id=123)

    p.write_message_begin("get", TMessageType.CALL, 0)
    p.write_struct(user)
    p.write_message_end()

    payload = {"soa": {}, "metas": {}, "iface": '', "method": "get",
               "ver": "1.0", "args": {"name": '"hello"', "id": "123"}}
    headers = set((b'', b'POST /rpc HTTP/1.1',
                   b'Connection: Keep-Alive',
                   b'Host: ',
                   b'Accept-Encoding: identity',
                   ('Content-Length: %d' % len(json.dumps(payload))).encode("ascii"),  # noqa
                   b'Content-Encoding: UTF-8',
                   b'Content-type: application/json'))

    val = t.getvalue().split(b"\r\n")

    assert headers == set(val[:-1])
    assert payload == json.loads(val[-1].decode("utf-8"))


def test_read_message(res_struct, http_entity):
    result = {"name": "hello", "id": 123}

    payload = {
        "ver": "1.0",
        "soa": {"req": None},
        "result": json.dumps(result),
        "ex": None
    }

    http_entity.length = 96
    http_entity.payload = payload

    t = TMemoryBuffer(http_entity.data)
    p = THTTPJsonProtocol(t)
    p.http._HTTPConnection__state = httplib._CS_REQ_SENT
    p.http.connect()

    r = res_struct().Result()

    p.read_message_begin()
    p.read_struct(r)
    p.read_message_end()

    assert r.success == User(name="hello", id=123)


def test_read_message_with_ex(res_struct, http_entity):
    payload = {
        "ver": "1.0", "soa": {"req": None}, "result": None,
        "ex": {
            "cl": "user.UserException",
            "fields": {"Code": "code"},
            "msg": "user not exist"
        }
    }

    http_entity.length = 141
    http_entity.payload = payload

    t = TMemoryBuffer(http_entity.data)
    p = THTTPJsonProtocol(t)
    p.http._HTTPConnection__state = httplib._CS_REQ_SENT
    p.http.connect()

    r = res_struct(spec=(TType.STRUCT, "exc", UserException, False)).Result()

    p.read_message_begin()
    p.read_struct(r)
    p.read_message_end()

    assert r.exc == UserException(cl="user.UserException",
                                  fields={"Code": "code"},
                                  msg="user not exist")


def test_read_message_with_ex_raised(res_struct, http_entity):
    payload = {
        "ver": "1.0", "soa": {"req": None}, "result": None,
        "ex": {
            "cl": "user.UserException",
            "fields": {"Code": "code"},
            "msg": "user not exist"
        }
    }

    http_entity.length = 141
    http_entity.payload = payload

    t = TMemoryBuffer(http_entity.data)
    p = THTTPJsonProtocol(t)
    p.http._HTTPConnection__state = httplib._CS_REQ_SENT
    p.http.connect()

    r = res_struct().Result()

    with pytest.raises(HTTPJsonException) as exc:
        p.read_message_begin()
        p.read_struct(r)
        p.read_message_end()
    assert "Undefined exception" in str(exc.value)


def test_read_message_with_none_field(res_struct, http_entity):
    result = {"name": "hello", "id": None}

    payload = {
        "ver": "1.0",
        "soa": {"req": None},
        "result": json.dumps(result),
        "ex": None
    }

    http_entity.length = len(json.dumps(payload))
    http_entity.payload = payload

    t = TMemoryBuffer(http_entity.data)
    p = THTTPJsonProtocol(t)
    p.http._HTTPConnection__state = httplib._CS_REQ_SENT
    p.http.connect()

    r = res_struct().Result()

    p.read_message_begin()
    p.read_struct(r)
    p.read_message_end()

    assert r.success == User(name="hello", id=None)
