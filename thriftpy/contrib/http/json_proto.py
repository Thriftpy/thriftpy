# -*- coding: utf-8 -*-

"""
http/json protocol
==================

http headers:

    Content-Length
    Content-Encoding: UTF-8
    Content-Type: application/json


thrift -> json:

    struct User {
        1: string name
        2: i32 id
    }

    struct Info {
        1: string f1
        2: i32 f2
        3: list<string> f3
        4: map<string, i32> f4
        5: User f5
    }

    =>

    {
        "f1": "hello",
        "f2": 123,
        "f3": ["a", "b", "c"],
        "f4": {"foo": 34, "bar": 123},
        "f5": {"name": "jane", "id": 10032}
    }

args:
    def ping(a, b, c):
        pass

    c.ping(23, "ping", User(name="jane", id=10032))

    =>

    {"a": "23", "b": '"ping"', "c": "{\"name\": \"jane\", \"id\": 10032}"}
"""


from __future__ import absolute_import

try:
    import httplib
except ImportError:
    import http.client as httplib

import cgi
import json

from thriftpy.protocol.exc import TProtocolException
from thriftpy.protocol.json import JsonConverter
from thriftpy.thrift import TMessageType, TType, TException

VERSION = "1.0"


class HTTPJsonException(TException):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return self.msg


class _JsonHTTP(httplib.HTTPConnection):
    def __init__(self, trans, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, '', *args, **kwargs)

        self.trans = trans

    def getresponse(self, *args, **kwargs):
        try:
            return httplib.HTTPConnection.getresponse(self, *args, **kwargs)
        except:
            self.close()
            raise

    def connect(self):
        if self.trans.is_open():
            self.trans.close()
        self.trans.open()
        self.sock = _Stream(self.trans)


class _Stream(object):
    def __init__(self, stream):
        self.stream = stream

    def _read(self, size):
        try:
            return self.stream.read(size)
        except:
            self.clean()
            raise

    def _write(self, data):
        try:
            self.stream.write(data)
        except:
            self.clean()
            raise

    def makefile(self, *args, **kwargs):
        return self

    def readline(self, size=-1):
        res = []
        data = None
        while data != b'\n':
            if len(res) == size:
                break

            data = self._read(1)
            if not data:
                break
            res.append(data)
        return b''.join(res)

    def clean(self):
        try:
            self.stream.clean()
        except Exception:
            pass

    def close(self):
        pass

    def read(self, size=-1):
        if size < 0:
            raise HTTPJsonException("`size` must be greater or equal than 0")
        return self._read(size)

    def sendall(self, data):
        self._write(data)


class Converter(JsonConverter):
    COMPLEX = (TType.STRUCT, TType.SET, TType.LIST, TType.MAP)

    @classmethod
    def json_map(cls, val, spec):
        key_type, key_spec = cls.parse_spec(spec[0], True)

        if key_type in cls.COMPLEX:
            raise TProtocolException("%r in map key, not supported" %
                                     TType._VALUES_TO_NAMES[key_type])

        value_type, value_spec = cls.parse_spec(spec[1], True)

        res = {}
        for k, v in val.items():
            key = str(cls.json_value(key_type, k, None))
            res[key] = cls.json_value(value_type, v, value_spec)
        return res

    @classmethod
    def thrift_map(cls, val, spec):
        res = {}

        key_type, key_spec = cls.parse_spec(spec[0], True)
        value_type, value_spec = cls.parse_spec(spec[1], True)

        for k, v in val.items():
            key = cls.thrift_value(key_type, k, key_spec)
            res[key] = cls.thrift_value(value_type, v, value_spec)

        return res


def serialize_args(struct):
    args = {}

    for fid in sorted(struct.thrift_spec):
        field_spec = struct.thrift_spec[fid]

        ttype, field_name, type_spec = Converter.parse_spec(field_spec)

        v = getattr(struct, field_name)
        if v is not None:
            v = Converter.json_value(ttype, v, type_spec)

        args[field_name] = json.dumps(v)

    return args


class THTTPJsonProtocol(object):
    """http/json protocol

    .. note::

        This protocol can only be used at client side!
    """
    def __init__(self, trans, uri="/rpc", keep_alive=True):
        self.trans = trans
        self.uri = uri

        self.http = _JsonHTTP(self.trans)

        self._reset_data()

        self.headers = {
            "Content-Length": 0,
            "Content-Encoding": "UTF-8",
            "Content-type": "application/json",
        }
        if keep_alive:
            self.headers["Connection"] = "Keep-Alive"

        self._writing = False

    def _reset_data(self):
        self._data = {"ver": VERSION, "method": '', "args": {}}
        self._meta = {"soa": {}, "iface": '', "metas": {}}

    def read_message_begin(self):
        response = self.http.getresponse()
        try:
            data = response.read()
        except Exception:
            self.http.close()
            raise

        content_type, encoding = response.getheader("Content-Type"), "utf-8"
        if content_type:
            content_type, params = cgi.parse_header(content_type)
            encoding = params.get("charset", "utf-8")

        status_code = response.status
        if status_code != 200:
            try:
                data = data.decode(encoding)
            except Exception:
                pass
            raise httplib.HTTPException("%d %s, %s" % (
                status_code, httplib.responses[status_code], data))

        assert content_type == "application/json", "Content type not json"
        payload = json.loads(data.decode(encoding))

        assert payload["ver"] == VERSION, "Version mismatch"

        self._payload = payload

        return '', TMessageType.REPLY, None

    def read_message_end(self):
        self._payload = None

    def write_metadata(self, **kwargs):
        self._meta.update(kwargs)

    def write_message_begin(self, name, ttype, seqid):
        self._data["method"] = name
        self._writing = True

    def write_message_end(self):
        assert self._writing
        self._writing = False

        try:
            self._data.update(self._meta)
            data = json.dumps(self._data).encode("utf-8")
        finally:
            self._reset_data()

        self.headers["Content-Length"] = len(data)
        self.http.request("POST", self.uri, body=data, headers=self.headers)

    def read_struct(self, obj):
        assert hasattr(self, "_payload") and self._payload

        res = self._payload["result"]
        res = self._safe_json_loads(res)

        ex = self._payload.get("ex")
        if ex:
            fields = ex.get("fields", {})
            for k, v in fields.items():
                fields[k] = self._safe_json_loads(v)

            name = self._get_thrift_exception_name(obj.thrift_spec, ex["cl"])
            if not name:
                raise HTTPJsonException(
                    "Undefined exception %s(%r) received." % (
                        ex["cl"], ex["msg"]))
            res = {name: ex}
        else:
            res = {"success": res}

        res = Converter.thrift_struct(res, obj)
        return res

    def write_struct(self, obj):
        assert self._writing

        self._data["args"] = serialize_args(obj)

    @staticmethod
    def _get_thrift_exception_name(spec, ex):
        name = ex.rsplit('.', 1)[-1]
        for i, v in spec.items():
            if i == 0 or len(v) <= 3:
                continue
            if name == v[2].__name__:
                return v[1]

    @staticmethod
    def _safe_json_loads(text):
        try:
            res = json.loads(text)
        except (ValueError, TypeError):
            res = text
        return res


class THTTPJsonProtocolFactory(object):
    def get_protocol(self, trans, uri="/rpc"):
        return THTTPJsonProtocol(trans, uri)
