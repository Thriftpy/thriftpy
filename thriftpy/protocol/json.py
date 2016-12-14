# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
import struct

from thriftpy.thrift import TType, TDecodeException

from .exc import TProtocolException

VERSION = 1


class JsonConverter(object):
    """thrift to json, json to thrift converter.

        struct <=> {"field_name": field_value}
        map    <=> {"key": key, "value": value}
        list   <=> [val, val]
        bool   <=> true/false
        int, double, string
    """
    INTEGER = (TType.BYTE, TType.I16, TType.I32, TType.I64)
    FLOAT = (TType.DOUBLE,)

    @staticmethod
    def parse_spec(spec, field=False):
        if field:
            if not isinstance(spec, (list, tuple)):
                ttype, type_spec = spec, None
            else:
                ttype, type_spec = spec
            return ttype, type_spec

        ttype, name = spec[:2]
        type_spec = None if len(spec) <= 3 else spec[2]
        return ttype, name, type_spec

    @classmethod
    def json_value(cls, ttype, val, spec=None):
        if ttype in cls.INTEGER or ttype in cls.FLOAT or ttype == TType.STRING:
            return val

        if ttype == TType.BOOL:
            return True if val else False

        if ttype == TType.STRUCT:
            return cls.json_struct(val)

        if ttype in (TType.SET, TType.LIST):
            return cls.json_list(val, spec)

        if ttype == TType.MAP:
            return cls.json_map(val, spec)

    @classmethod
    def json_map(cls, val, spec):
        res = []

        key_type, key_spec = cls.parse_spec(spec[0], True)
        value_type, value_spec = cls.parse_spec(spec[1], True)

        for k, v in val.items():
            res.append({"key": cls.json_value(key_type, k, key_spec),
                        "value": cls.json_value(value_type, v, value_spec)})

        return res

    @classmethod
    def json_list(cls, val, spec):
        elem_type, type_spec = cls.parse_spec(spec, True)
        return [cls.json_value(elem_type, i, type_spec) for i in val]

    @classmethod
    def json_struct(cls, val):
        outobj = {}
        for fid, field_spec in val.thrift_spec.items():
            ttype, field_name, field_type_spec = cls.parse_spec(field_spec)

            v = getattr(val, field_name)
            if v is None:
                continue

            outobj[field_name] = cls.json_value(ttype, v, field_type_spec)

        return outobj

    @classmethod
    def thrift_value(cls, ttype, val, spec=None):
        if ttype in cls.INTEGER:
            return int(val)

        if ttype in cls.FLOAT:
            return float(val)

        if ttype in (TType.STRING, TType.BOOL):
            return val

        if ttype == TType.STRUCT:
            return cls.thrift_struct(val, spec())

        if ttype in (TType.SET, TType.LIST):
            return cls.thrift_list(val, spec)

        if ttype == TType.MAP:
            return cls.thrift_map(val, spec)

    @classmethod
    def thrift_map(cls, val, spec):
        res = {}

        key_type, key_spec = cls.parse_spec(spec[0], True)
        value_type, value_spec = cls.parse_spec(spec[1], True)

        for v in val:
            key = cls.thrift_value(key_type, v["key"], key_spec)
            res[key] = cls.thrift_value(value_type, v["value"], value_spec)

        return res

    @classmethod
    def thrift_list(cls, val, spec):
        elem_type, type_spec = cls.parse_spec(spec, True)
        return [cls.thrift_value(elem_type, i, type_spec) for i in val]

    @classmethod
    def thrift_struct(cls, val, obj):
        if not val:
            return obj

        for fid, field_spec in obj.thrift_spec.items():
            ttype, field_name, field_type_spec = cls.parse_spec(field_spec)

            raw_val = val.get(field_name)
            if raw_val is None:
                continue

            try:
                v = cls.thrift_value(ttype, raw_val, field_type_spec)
            except (TypeError, ValueError, AttributeError):
                raise TDecodeException(obj.__class__.__name__, fid, field_name,
                                       raw_val, ttype, field_type_spec)
            setattr(obj, field_name, v)
        return obj


class TJSONProtocol(object):
    """A JSON protocol.

    The message in the transport are encoded as this: 4 bytes represents
    the length of the json object and immediately followed by the json object.

        '\x00\x00\x00+' '{"payload": {}, "metadata": {"version": 1}}'

    the 4 bytes are the bytes representation of an integer and is encoded in
    big-endian.
    """
    def __init__(self, trans):
        self.trans = trans
        self._meta = {"version": VERSION}
        self._data = None

    def _write_len(self, x):
        self.trans.write(struct.pack('!I', int(x)))

    def _read_len(self):
        l = self.trans.read(4)
        return struct.unpack('!I', l)[0]

    def read_message_begin(self):
        size = self._read_len()
        self._data = json.loads(self.trans.read(size).decode("utf-8"))
        metadata = self._data["metadata"]

        version = int(metadata["version"])
        if version != VERSION:
            raise TProtocolException(
                type=TProtocolException.BAD_VERSION,
                message="Bad version in read_message_begin:{}".format(version))

        return metadata["name"], metadata["ttype"], metadata["seqid"]

    def read_message_end(self):
        pass

    def write_message_begin(self, name, ttype, seqid):
        self._meta.update({"name": name, "ttype": ttype, "seqid": seqid})

    def write_message_end(self):
        pass

    def read_struct(self, obj):
        if not self._data:
            size = self._read_len()
            self._data = json.loads(self.trans.read(size).decode("utf-8"))

        res = JsonConverter.thrift_struct(self._data["payload"], obj)
        self._data = None
        return res

    def write_struct(self, obj):
        data = json.dumps({
            "metadata": self._meta,
            "payload": JsonConverter.json_struct(obj)
        })

        self._write_len(len(data))
        self.trans.write(data.encode("utf-8"))


class TJSONProtocolFactory(object):
    def get_protocol(self, trans):
        return TJSONProtocol(trans)
