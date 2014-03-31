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
"""


# constants
LBRACE, RBRACE, COLON, SEMI, COMMA, EQ = map(pa.Suppress, "{}:;,=")

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
const = _const + ttype + identifier("name") + EQ + value("value")


# enum parser
enum_value = pa.Group(identifier('name') + pa.Optional(EQ + integer('value')))
enum_list = pa.Group(enum_value + pa.ZeroOrMore(COMMA + enum_value) + pa.Optional(COMMA))
enum = _enum + identifier("enum") + LBRACE + enum_list("names") + RBRACE


# struct parser
category = pa.Literal("required") | pa.Literal("optional")
struct_field = pa.Group(integer("id") + COLON + category + ttype("ttype") + identifier("name") + pa.Optional(COMMA))
struct_fields = pa.Group(pa.OneOrMore(struct_field))
struct = _struct + identifier("struct") + LBRACE + struct_fields("fields") + RBRACE
