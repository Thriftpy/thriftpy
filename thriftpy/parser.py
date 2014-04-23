# -*- coding: utf-8 -*-
# flake8: noqa

import functools
import itertools
import os
import sys
import types

import pyparsing as pa


from .thrift import TType, TPayload, TException


def _or(*iterable):
    return functools.reduce(lambda x, y: x | y, iterable)


def parse(schema):
    result = {}

    # constants
    LPAR, RPAR, LBRACK, RBRACK, LBRACE, RBRACE, LABRACK, RABRACK, COLON, SEMI, COMMA, EQ = map(pa.Suppress, "()[]{}<>:;,=")

    # keywords
    _typedef, _const, _enum, _struct, _exception, _service = map(pa.Keyword, ("typedef", "const", "enum", "struct", "exception", "service"))

    # comment match
    single_line_comment = (pa.Suppress("//") | pa.Suppress("#")) + pa.restOfLine

    # general tokens
    identifier = pa.Word(pa.alphanums + '_')

    # general value
    value = pa.Forward()
    integer_ = pa.Word(pa.nums)
    string_ = pa.quotedString
    list_ = LBRACK + pa.Group(value + pa.ZeroOrMore(COMMA + value)) + RBRACK
    value << _or(integer_, string_, list_)

    # scan for possible user defined types
    _typedef_prefix = _typedef + identifier + pa.Optional(pa.nestedExpr(opener='<', closer='>'))
    scan_utypes = _or(_typedef_prefix, _enum, _struct, _exception) + identifier
    utypes = map(pa.Keyword, (t[-1] for t, _, _ in scan_utypes.scanString(schema)))

    # ttypes
    ttype = pa.Forward()
    t_list = pa.Group(pa.Keyword("list")("ttype") + LABRACK + ttype('v') + RABRACK)
    t_map = pa.Group(pa.Keyword("map")("ttype") + LABRACK + ttype('k') + COMMA + ttype('v') + RABRACK)
    orig_types = _or(t_list, t_map, *map(pa.Keyword, ("bool", "byte", "i16", "i32", "i64", "double", "string")))
    ttype << _or(orig_types, *utypes)

    # typedef parser
    typedef = _typedef + orig_types("ttype") + identifier("name")
    result["typedefs"] = {t.name: t.ttype for t, _, _ in typedef.scanString(schema)}

    # const parser
    const = _const + ttype("ttype") + identifier("name") + EQ + value("value")
    result["consts"] = {c.name: c.value for c, _, _ in const.scanString(schema)}

    # enum parser
    enum_value = pa.Group(identifier('name') + pa.Optional(EQ + integer_('value')) + pa.Optional(COMMA))
    enum_list = pa.Group(pa.OneOrMore(enum_value))("members")
    enum = _enum + identifier("name") + LBRACE + enum_list + RBRACE
    enum.ignore(single_line_comment)
    result["enums"] = {e.name: e for e, _, _ in enum.scanString(schema)}

    # struct parser
    category = _or(*map(pa.Literal, ("required", "optional")))
    struct_field = pa.Group(integer_("id") + COLON + pa.Optional(category) + ttype("ttype") + identifier("name") + pa.Optional(COMMA))
    struct_members = pa.Group(pa.OneOrMore(struct_field))("members")
    struct = _struct + identifier("name") + LBRACE + struct_members + RBRACE
    struct.ignore(single_line_comment)
    # struct defines is ordered
    result["structs"] = [s for s, _, _ in struct.scanString(schema)]

    # exception parser
    exception = _exception + identifier("name") + LBRACE + struct_members + RBRACE
    exception.ignore(single_line_comment)
    result["exceptions"] = [s for s, _, _ in exception.scanString(schema)]

    # service parser
    ftype = _or(ttype, pa.Keyword("void"))
    api_param = pa.Group(integer_("id") + COLON + ttype("ttype") + identifier("name") + pa.Optional(COMMA))
    api_params = pa.Group(pa.ZeroOrMore(api_param))
    service_api = pa.Group(ftype("ttype") + identifier("name") + LPAR + api_params("params") + RPAR + pa.Optional(pa.Keyword("throws") + LPAR + api_params("throws") + RPAR) + pa.Optional(SEMI | COMMA))
    service_apis = pa.Group(pa.OneOrMore(service_api))("apis")
    service = _service + identifier("name") + LBRACE + service_apis + RBRACE
    service.ignore(single_line_comment)
    service.ignore(pa.cStyleComment)
    result["services"] = [s for s, _, _ in service.scanString(schema)]

    return result


def load(thrift_file):
    module_name = thrift_file[:thrift_file.find('.')]
    with open(thrift_file, 'r') as f:
        result = parse(f.read())
    struct_names = [s.name for s in itertools.chain(result["structs"],
                                                    result["exceptions"])]

    # load thrift schema as module
    thrift_schema = types.ModuleType(module_name)

    def _ttype(t):
        if isinstance(t, str):
            if t in struct_names:
                return TType.STRUCT, getattr(thrift_schema, t)
            elif t in result["enums"]:
                return TType.I32
            elif t in result["typedefs"]:
                return _ttype(result["typedefs"][t])
            else:
                return getattr(TType, t.upper())

        if t.ttype == "list":
            return TType.LIST, _ttype(t.v)
        elif t.ttype == "map":
            return TType.MAP, (_ttype(t.k), _ttype(t.v))
        else:
            raise Exception("ttype parse error: {0}".format(t))

    def _ttype_spec(ttype, name):
        ttype = _ttype(ttype)
        if isinstance(ttype, int):
            return ttype, name
        else:
            return ttype[0], name, ttype[1]

    # load consts
    for name, value in result["consts"].items():
        setattr(thrift_schema, name, value)

    # load enums
    for name, enum in result["enums"].items():
        enum_cls = type(name, (object, ), {})
        value = 0
        for m in enum.members:
            if m.value:
                value = int(m.value)
            else:
                value += 1
            setattr(enum_cls, m.name, value)
        setattr(thrift_schema, enum.name, enum_cls)

    # load structs
    for struct in result["structs"]:
        struct_cls = type(struct.name, (TPayload, ), {})
        thrift_spec = {}
        for m in struct.members:
            thrift_spec[int(m.id)] = _ttype_spec(m.ttype, m.name)
        setattr(struct_cls, "thrift_spec", thrift_spec)
        setattr(thrift_schema, struct.name, struct_cls)

    # load exceptions
    for exc in result["exceptions"]:
        exc_cls = type(exc.name, (TException, ), {})
        thrift_spec = {}
        for m in exc.members:
            thrift_spec[int(m.id)] = _ttype_spec(m.ttype, m.name)
        setattr(exc_cls, "thrift_spec", thrift_spec)
        setattr(thrift_schema, exc.name, exc_cls)

    # load services
    for service in result["services"]:
        service_cls = type(service.name, (object, ), {})
        thrift_services = []
        for api in service.apis:
            thrift_services.append(api.name)

            # args payload
            api_args_cls = type("%s_args" % api.name, (TPayload, ), {})
            api_args_spec = {}
            for param in api.params:
                api_args_spec[int(param.id)] = _ttype_spec(param.ttype,
                                                           param.name)
            setattr(api_args_cls, "thrift_spec", api_args_spec)
            setattr(service_cls, "%s_args" % api.name, api_args_cls)

            # result payload
            api_result_cls = type("%s_result" % api.name, (TPayload, ), {})
            if api.ttype == "void":
                api_result_spec = {}
            else:
                api_result_spec = {0: _ttype_spec(api.ttype, "success")}

            if hasattr(api, "throws"):
                for t in api.throws:
                    api_result_spec[int(t.id)] = _ttype_spec(t.ttype, t.name)

            setattr(api_result_cls, "thrift_spec", api_result_spec)
            setattr(service_cls, "%s_result" % api.name, api_result_cls)

        setattr(service_cls, "thrift_services", thrift_services)
        setattr(thrift_schema, service.name, service_cls)

    return thrift_schema


class ThriftImporter(object):
    def __init__(self, extension="_thrift"):
        self.extension = extension

    def __eq__(self, other):
        return self.__class__.__module__ == other.__class__.__module__ and \
            self.__class__.__name__ == other.__class__.__name__ and \
            self.extension == other.extension

    def install(self):
        sys.meta_path[:] = [x for x in sys.meta_path if self != x] + [self]

    def find_module(self, fullname, path=None):
        if fullname.endswith(self.extension):
            return self

    def load_module(self, fullname):
        if '.' in fullname:
            module_name, thrift_file = fullname.rsplit('.', 1)
            module = self._import_module(module_name)
            path_prefix = os.path.dirname(os.path.abspath(module.__file__))
            path = os.path.join(path_prefix, thrift_file)
        else:
            path = fullname
        filename = path.replace('_', '.', 1)
        thrift = load(filename)
        sys.modules[fullname] = thrift
        return thrift

    def _import_module(self, import_name):
        if '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
            return getattr(__import__(module, None, None, [obj]), obj)
        else:
            return __import__(import_name)
