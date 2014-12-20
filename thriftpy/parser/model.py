# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] < 3:
    bytes_ = bytes
else:
    bytes_ = lambda x: bytes(x, 'utf8')


class Thrift(dict):

    def __init__(self,
                 includes=None,
                 namespaces=None,
                 consts=None,
                 enums=None,
                 typedefs=None,
                 structs=None,
                 unions=None,
                 exceptions=None,
                 services=None):

        super(Thrift, self).__init__()

        if includes is None:
            includes = []
        if namespaces is None:
            namespaces = {}
        if consts is None:
            consts = {}
        if enums is None:
            enums = {}
        if typedefs is None:
            typedefs = {}
        if structs is None:
            structs = {}
        if unions is None:
            unions = {}
        if exceptions is None:
            exceptions = {}
        if services is None:
            services = {}

        self.includes = self['includes'] = includes
        self.namespaces = self['namespaces'] = namespaces
        self.consts = self['consts'] = consts
        self.enums = self['enums'] = enums
        self.typedefs = self['typedefs'] = typedefs
        self.structs = self['structs'] = structs
        self.unions = self['unions'] = unions
        self.exceptions = self['exceptions'] = exceptions
        self.services = self['services'] = services


class BaseType(str):
    pass


class BoolType(BaseType):

    cast = bool

    def __new__(self):
        return str.__new__(self, 'bool')


class ByteType(BaseType):

    cast = int

    def __new__(self):
        return str.__new__(self, 'byte')


class I16Type(BaseType):

    cast = int

    def __new__(self):
        return str.__new__(self, 'i16')


class I32Type(BaseType):

    cast = int

    def __new__(self):
        return str.__new__(self, 'i32')


class I64Type(BaseType):

    cast = int

    def __new__(self):
        return str.__new__(self, 'i64')


class DoubleType(BaseType):

    cast = float

    def __new__(self):
        return str.__new__(self, 'double')


class StringType(BaseType):

    cast = str

    def __new__(self):
        return str.__new__(self, 'string')


class BinaryType(BaseType):

    cast = bytes_

    def __new__(self):
        return str.__new__(self, 'binary')


class ContainerType(list):
    pass


class ListType(ContainerType):   # ['list', val_type]

    def cast(self, data):
        return list(map(self[1].cast, data))


class MapType(ContainerType):  # ['map', k_type, v_type]

    def cast(self, data):
        dct = {}
        keys = data.keys()

        for key in keys:
            dct[self[1].cast(key)] = self[2].cast(data[key])
        return dct


class SetType(ContainerType):  # ['set', v_type]

    def cast(self, data):
        return frozenset(map(self[1].cast, data))


BASE_TYPE_MAPS = {
    'bool': BoolType,
    'byte': ByteType,
    'i16': I16Type,
    'i32': I32Type,
    'i64': I64Type,
    'double': DoubleType,
    'string': StringType,
    'binary': BinaryType
}


class IdentifierValue(dict):
    def __init__(self, v):
        super(IdentifierValue, self).__init__()
        self.v = self['v'] = v


class Field(dict):

    def __init__(self, id, type, name, value=None, requirement=None):
        super(Field, self).__init__()
        self.id = self['id'] = id
        self.type = self['type'] = type
        self.name = self['name'] = name
        self.value = self['value'] = value
        self.requirement = self['requirement'] = requirement


class Function(dict):

    def __init__(self, type, name, fields=None, throws=None, oneway=False):
        super(Function, self).__init__()

        if fields is None:
            fields = []
        if throws is None:
            throws = []
        self.type = self['type'] = type
        self.name = self['name'] = name
        self.fields = self['fields'] = fields
        self.throws = self['throws'] = throws
        self.oneway = self['oneway'] = oneway


class Service(dict):

    def __init__(self, extends=None, apis=None):
        super(Service, self).__init__()

        if apis is None:
            apis = {}

        self.extends = self['extends'] = extends
        self.apis = self['apis'] = apis
