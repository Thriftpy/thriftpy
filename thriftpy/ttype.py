# -*- coding: utf-8 -*-

from __future__ import absolute_import

from ._compat import init_func_generator, with_metaclass


class TType(object):
    STOP = 0
    VOID = 1
    BOOL = 2
    BYTE = 3
    I08 = 3
    DOUBLE = 4
    I16 = 6
    I32 = 8
    I64 = 10
    STRING = 11
    UTF7 = 11
    BINARY = 11  # This here just for parsing. For all purposes, it's a string
    STRUCT = 12
    MAP = 13
    SET = 14
    LIST = 15
    UTF8 = 16
    UTF16 = 17

    _VALUES_TO_NAMES = {
        STOP: 'STOP',
        VOID: 'VOID',
        BOOL: 'BOOL',
        BYTE: 'BYTE',
        I08: 'BYTE',
        DOUBLE: 'DOUBLE',
        I16: 'I16',
        I32: 'I32',
        I64: 'I64',
        STRING: 'STRING',
        UTF7: 'STRING',
        BINARY: 'STRING',
        STRUCT: 'STRUCT',
        MAP: 'MAP',
        SET: 'SET',
        LIST: 'LIST',
        UTF8: 'UTF8',
        UTF16: 'UTF16'
    }


class TMessageType(object):
    CALL = 1
    REPLY = 2
    EXCEPTION = 3
    ONEWAY = 4


class TPayloadMeta(type):
    def __new__(cls, name, bases, attrs):
        if "default_spec" in attrs:
            attrs["__init__"] = init_func_generator(attrs.pop("default_spec"))
        return super(TPayloadMeta, cls).__new__(cls, name, bases, attrs)


def gen_init(cls, thrift_spec=None, default_spec=None):
    if thrift_spec is not None:
        cls.thrift_spec = thrift_spec

    if "default_spec" is not None:
        cls.__init__ = init_func_generator(default_spec)
    return cls


class TPayload(with_metaclass(TPayloadMeta, object)):

    def read(self, iprot):
        iprot.read_struct(self)

    def write(self, oprot):
        oprot.write_struct(self)

    def __repr__(self):
        l = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(l))

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.__dict__ == other.__dict__

    def __hash__(self):
        return super(TPayload, self).__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)


class TException(TPayload, Exception):
    """Base class for all thrift exceptions."""


class TApplicationException(TException):
    """Application level thrift exceptions."""

    thrift_spec = {
        1: (TType.STRING, 'message'),
        2: (TType.I32, 'type'),
    }

    UNKNOWN = 0
    UNKNOWN_METHOD = 1
    INVALID_MESSAGE_TYPE = 2
    WRONG_METHOD_NAME = 3
    BAD_SEQUENCE_ID = 4
    MISSING_RESULT = 5
    INTERNAL_ERROR = 6
    PROTOCOL_ERROR = 7

    def __init__(self, type=UNKNOWN, message=None):
        super(TApplicationException, self).__init__()
        self.type = type
        self.message = message

    def __str__(self):
        if self.message:
            return self.message

        if self.type == self.UNKNOWN_METHOD:
            return 'Unknown method'
        elif self.type == self.INVALID_MESSAGE_TYPE:
            return 'Invalid message type'
        elif self.type == self.WRONG_METHOD_NAME:
            return 'Wrong method name'
        elif self.type == self.BAD_SEQUENCE_ID:
            return 'Bad sequence ID'
        elif self.type == self.MISSING_RESULT:
            return 'Missing result'
        else:
            return 'Default (unknown) TApplicationException'
