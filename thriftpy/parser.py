import collections
import types
import sys

import pyparsing as pa


from thriftpy.thrift import TType, TPayload


example = """
const i16 DEFAULT = 10
const i16 MAX = 200

enum MessageStatus {
    VALID = 0,
    INVALID = 1,
}

struct Item {
    1: optional i32 id,
    2: optional string name,
}

service ExampleService {
    bool ping();
    string hello(1: string name);
}
"""


def parse(schema):

    # constants
    LBRACE, RBRACE, LBRACKET, RBRACKET, COLON, SEMI, COMMA, EQ = map(pa.Suppress, "{}():;,=")

    # keywords
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
    integer = pa.Word(pa.nums)
    value = pa.Word(pa.alphas + pa.nums)

    # const parser
    const = pa.Group(_const + ttype + identifier("name") + EQ + value("value"))
    consts = pa.Group(pa.OneOrMore(const))("consts")

    # enum parser
    enum_value = pa.Group(identifier('name') + pa.Optional(EQ + integer('value')))
    enum_list = pa.Group(enum_value + pa.ZeroOrMore(COMMA + enum_value) + pa.Optional(COMMA))("members")
    enum = pa.Group(_enum + identifier("name") + LBRACE + enum_list + RBRACE)
    enums = pa.Group(pa.OneOrMore(enum))("enums")

    # struct parser
    category = pa.Literal("required") | pa.Literal("optional")
    struct_field = pa.Group(integer("id") + COLON + category + ttype("ttype") + identifier("name") + pa.Optional(COMMA))
    struct_members = pa.Group(pa.OneOrMore(struct_field))("members")
    struct = pa.Group(_struct + identifier("name") + LBRACE + struct_members + RBRACE)
    structs = pa.Group(pa.OneOrMore(struct))("structs")


    # service parser
    api_param = pa.Group(integer("id") + COLON + ttype("ttype") + identifier("name"))
    api_params = pa.Group(pa.Optional(api_param) + pa.ZeroOrMore(COMMA + api_param))("params")
    service_api = pa.Group(ttype("ttype") + identifier("api") + LBRACKET + api_params + RBRACKET + SEMI)
    service_apis = pa.Group(pa.OneOrMore(service_api))("apis")
    service = pa.Group(_service + identifier("name") + LBRACE + service_apis + RBRACE)
    services = pa.Group(pa.OneOrMore(service))("services")

    # entry
    parser = pa.OneOrMore(consts | enums | structs | services)

    return parser.parseString(schema)


def load(thrift_file):
    module_name = thrift_file[:thrift_file.find('.')]
    with open(thrift_file, 'r') as f:
        result = parse(f.read())

    thrift_schema = types.ModuleType(module_name)
    _ttype = lambda t: getattr(TType, t.upper())

    # load consts
    for const in result.consts:
        setattr(thrift_schema, const.name, const.value)

    # load enums
    for enum in result.enums:
        enum_cls = type(enum.name, (object, ), {})
        for m in enum.members:
            setattr(enum_cls, m.name, m.value)
        setattr(thrift_schema, enum.name, enum_cls)

    # load structs
    for struct in result.structs:
        struct_cls = type(struct.name, (TPayload, ), {})
        thrift_spec = {}
        for m in struct.members:
            thrift_spec[m.id] = _ttype(m.ttype), m.name, None, None
        setattr(struct_cls, "thrift_spec", thrift_spec)
        setattr(thrift_schema, struct.name, struct_cls)

    # load services
    for service in result.services:
        service_cls = type(service.name, (object, ), {})
        thrift_services = []
        for api in service.apis:
            thrift_services.append(api.name)

            api_args_cls = type("%s_args" % api.name, (TPayload, ), {})
            api_args_spec = {}
            for param in api.params:
                api_args_spec[param.id] = param.ttype, param.name, None, None
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
