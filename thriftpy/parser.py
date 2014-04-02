# flake8: noqa

import collections
import types
import sys

import pyparsing as pa


from .thrift import TType, TPayload


example = """
typedef string json

const i16 DEFAULT = 10
const string HELLO = "hello"
const json DETAIL = "{'hello': 'world'}"

enum MessageStatus {
    VALID = 0,
    INVALID = 1,
}

struct TItem {
    1: optional i32 id,
    2: optional string name,
    3: optional json detail,
}

service ExampleService {
    bool ping();
    string hello(1: string name);
    TItem make(1: string name, 2: json detail);
}
"""


def parse(schema):
    result = collections.defaultdict(dict)
    typemap = {}

    # constants
    LPAR, RPAR, LBRACK, RBRACK, LBRACE, RBRACE, COLON, SEMI, COMMA, EQ = map(pa.Suppress, "()[]{}:;,=")

    # keywords
    _typedef = pa.Keyword("typedef")
    _const = pa.Keyword("const")
    _enum = pa.Keyword("enum")
    _struct = pa.Keyword("struct")
    _service = pa.Keyword("service")

    # ttypes
    bool_ = pa.Keyword("bool")
    byte_ = pa.Keyword("byte")
    i16_ = pa.Keyword("i16")
    i32_ = pa.Keyword("i32")
    i64_ = pa.Keyword("i64")
    double_ = pa.Keyword("double")
    string_ = pa.Keyword("string")
    ttype = bool_ | byte_ | i16_ | i32_ | i64_ | double_ | string_

    # general tokens
    identifier = pa.Word(pa.alphas)

    value = pa.Forward()
    integer_ = pa.Word(pa.nums)
    string_ = pa.quotedString
    list_ = LBRACK + pa.Group(value + pa.ZeroOrMore(COMMA + value)) + RBRACK
    value << (integer_ | string_ | list_)

    # typedef parser
    typedef = _typedef + ttype("ttype") + identifier("name")
    for t, _, _ in typedef.scanString(schema):
        result["typedefs"][t.name] = t.ttype
        typemap[t.name] = t.ttype

    # const parser
    utype = ttype
    for t in typemap:
        utype |= pa.Keyword(t)

    const = _const + utype + identifier("name") + EQ + value("value")
    result["consts"] = {c.name: c for c, _, _ in const.scanString(schema)}

    # enum parser
    enum_value = pa.Group(identifier('name') + pa.Optional(EQ + integer_('value')))
    enum_list = pa.Group(enum_value + pa.ZeroOrMore(COMMA + enum_value) + pa.Optional(COMMA))("members")
    enum = _enum + identifier("name") + LBRACE + enum_list + RBRACE
    result["enums"] = {e.name: e for e, _, _ in enum.scanString(schema)}

    # struct parser
    category = pa.Literal("required") | pa.Literal("optional")
    struct_field = pa.Group(integer_("id") + COLON + category + utype("ttype") + identifier("name") + pa.Optional(COMMA))
    struct_members = pa.Group(pa.OneOrMore(struct_field))("members")
    struct = _struct + identifier("name") + LBRACE + struct_members + RBRACE
    result["structs"] = {s.name: s for s, _, _ in struct.scanString(schema)}

    # service parser
    ftype = utype | pa.Keyword("oneway") | pa.Keyword("void")
    for struct in result["structs"]:
        ftype |= pa.Keyword(struct)

    api_param = pa.Group(integer_("id") + COLON + utype("ttype") + identifier("name"))
    api_params = pa.Group(pa.Optional(api_param) + pa.ZeroOrMore(COMMA + api_param))("params")
    service_api = pa.Group(ftype("ttype") + identifier("name") + LPAR + api_params + RPAR + SEMI)
    service_apis = pa.Group(pa.OneOrMore(service_api))("apis")
    service = _service + identifier("name") + LBRACE + service_apis + RBRACE
    result["services"] = {s.name: s for s, _, _ in service.scanString(schema)}

    return result


def load(thrift_file):
    module_name = thrift_file[:thrift_file.find('.')]
    with open(thrift_file, 'r') as f:
        result = parse(f.read())

    thrift_schema = types.ModuleType(module_name)
    _ttype = lambda t: getattr(TType, t.upper())

    # load consts
    for const in result["consts"].values():
        setattr(thrift_schema, const.name, const.value)

    # load enums
    for enum in result["enums"].values():
        enum_cls = type(enum.name, (object, ), {})
        for m in enum.members:
            setattr(enum_cls, m.name, m.value)
        setattr(thrift_schema, enum.name, enum_cls)

    # load structs
    for struct in result["structs"].values():
        struct_cls = type(struct.name, (TPayload, ), {})
        thrift_spec = {}
        for m in struct.members:
            thrift_spec[m.id] = _ttype(m.ttype), m.name, None, None
        setattr(struct_cls, "thrift_spec", thrift_spec)
        setattr(thrift_schema, struct.name, struct_cls)

    # load services
    for service in result["services"].values():
        service_cls = type(service.name, (object, ), {})
        thrift_services = []
        for api in service.apis:
            thrift_services.append(api.name)

            api_args_cls = type("%s_args" % api.name, (TPayload, ), {})
            api_args_spec = {}
            for param in api.params:
                api_args_spec[int(param.id)] = (_ttype(param.ttype),
                                           param.name, None, None)
            setattr(api_args_cls, "thrift_spec", api_args_spec)
            setattr(service_cls, "%s_args" % api.name, api_args_cls)

            api_result_cls = type("%s_result" % api.name, (TPayload, ), {})
            api_result_spec = {0: (_ttype(api.ttype), "success", None, None)}
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
        filename = fullname.replace('_', '.', 1)
        module = load(filename)
        sys.modules[fullname] = module
        return module
