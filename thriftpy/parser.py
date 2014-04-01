# flake8: noqa

import pyparsing as pa


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


# constants
LBRACE, RBRACE, LBRACKET, RBRACKET, COLON, SEMI, COMMA, EQ = map(pa.Suppress, "{}():;,=")

# keywords
_const = pa.Suppress("const")
_enum = pa.Suppress("enum")
_struct = pa.Suppress("struct")
_service = pa.Suppress("service")


# ttypes
bool_ = pa.Suppress("bool")
byte_ = pa.Suppress("byte")
i16_ = pa.Suppress("i16")
i32_ = pa.Suppress("i32")
i64_ = pa.Suppress("i64")
double_ = pa.Suppress("double")
string_ = pa.Suppress("string")
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
enum_list = pa.Group(enum_value + pa.ZeroOrMore(COMMA + enum_value) + pa.Optional(COMMA))("names")
enum = pa.Group(_enum + identifier("enum") + LBRACE + enum_list + RBRACE)
enums = pa.Group(pa.OneOrMore(enum))("enums")


# struct parser
category = pa.Literal("required") | pa.Literal("optional")
struct_field = pa.Group(integer("id") + COLON + category + ttype("ttype") + identifier("name") + pa.Optional(COMMA))
struct_fields = pa.Group(pa.OneOrMore(struct_field))("fields")
struct = pa.Group(_struct + identifier("struct") + LBRACE + struct_fields + RBRACE)
structs = pa.Group(pa.OneOrMore(struct))("structs")


# service parser
api_param = pa.Group(integer("id") + COLON + ttype("ttype") + identifier("name"))
api_params = pa.Group(pa.Optional(api_param) + pa.ZeroOrMore(COMMA + api_param))("params")
service_api = pa.Group(ttype + identifier("api") + LBRACKET + api_params + RBRACKET + SEMI)
service_apis = pa.Group(pa.OneOrMore(service_api))("apis")
service = pa.Group(_service + identifier("service") + LBRACE + service_apis + RBRACE)
services = pa.Group(pa.OneOrMore(service))("services")


# entry
thrift_parser = pa.OneOrMore(consts | enums | structs | services)
