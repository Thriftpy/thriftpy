# -*- coding: utf-8 -*-

import sys

if sys.version < '3':
    bytes_ = bytes
else:
    bytes_ = lambda x: bytes(x, 'utf8')


class TBase(str):
    name = None
    __new__ = lambda self: str.__new__(self, self.name)


class TBool(TBase):
    name = 'bool'
    cast = bool


class TByte(TBase):
    name = 'byte'
    cast = int


class TI16(TBase):
    name = 'i16'
    cast = int


class TI32(TBase):
    name = 'i32'
    cast = int


class TI64(TBase):
    name = 'i64'
    cast = int


class TDouble(TBase):
    name = 'double'
    cast = float


class TString(TBase):
    name = 'string'
    cast = str


class TBinary(TBase):
    name = 'binary'
    cast = bytes_


class TContainer(list):
    pass


class TList(TContainer):  # ['list', val_tp]

    def cast(self, data):
        return list(map(self[1].cast, data))


class TMap(TContainer):  # ['map', key_tp, val_tp]

    def cast(self, data):
        dct = {}

        for key in data:
            dct[self[1].cast(key)] = self[2].cast(data[key])
        return dct


class TSet(TContainer):  # ['set', val_tp]

    def cast(self, data):
        return set(map(self[1].cast, data))


BASE_TYPE_MAPS = {
    'bool': TBool,
    'byte': TByte,
    'i16': TI16,
    'i32': TI32,
    'i64': TI64,
    'double': TDouble,
    'string': TString,
    'binary': TBinary
}


class TType(dict):
    pass


class TTypeDef(TType):
    ttype = 'typedef'


class TEnum(TType):
    ttype = 'enum'


class TStruct(TType):
    ttype = 'struct'


class TException(TType):
    ttype = 'exception'


class TService(TType):
    ttype = 'service'


class TField(dict):
    pass


class TFunction(dict):
    pass
