# -*- coding: utf-8 -*-

"""
IDL Ref:
    https://thrift.apache.org/docs/idl
"""

from __future__ import absolute_import

from ply import yacc

from .lexer import tokens, lexer  # noqa
from .types import *  # noqa
from .exc import ThriftGrammerError


def p_error(p):
    raise ThriftGrammerError('Grammer error %r at line %d' %
                             (p.value, p.lineno))


def p_start(p):
    '''start : header definition'''


def p_header(p):
    '''header : header_unit_ header
              |'''


def p_header_unit_(p):
    '''header_unit_ : header_unit ';'
                    | header_unit'''


def p_header_unit(p):
    '''header_unit : include
                   | namespace'''


def p_include(p):
    '''include : INCLUDE LITERAL'''
    thrift.setdefault('includes', set()).add(p[2])


def p_namespace(p):
    '''namespace : NAMESPACE namespace_scope IDENTIFIER'''
    thrift.setdefault('namespaces', {})[p[3]] = p[2]


def p_namespace_scope(p):
    '''namespace_scope : '*'
                       | IDENTIFIER'''
    p[0] = p[1]


def p_sep(p):
    '''sep : ','
           | ';'
    '''


def p_definition(p):
    '''definition : definition definition_unit_
                  |'''


def p_definition_(p):
    '''definition_unit_ : definition_unit ';'
                        | definition_unit'''


def p_definition_unit(p):
    '''definition_unit : const
                       | ttype
    '''


def p_const(p):
    '''const : CONST field_type IDENTIFIER '=' const_value'''
    thrift.setdefault('constants', {})[p[3]] = p[2].cast(p[5])


def p_const_value(p):
    '''const_value : INTCONSTANT
                   | DUBCONSTANT
                   | LITERAL
                   | BOOLCONSTANT
                   | const_list
                   | const_map
                   | const_ref'''
    p[0] = p[1]


def p_const_list(p):
    '''const_list : '[' const_value_seq ']' '''
    p[0] = p[2]


def p_const_value_seq(p):
    '''const_value_seq : const_value sep const_value_seq
                       | const_value const_value_seq
                       |'''
    _parse_seq(p)


def p_const_map(p):
    '''const_map : '{' const_map_seq '}' '''
    p[0] = dict(p[2])


def p_const_map_seq(p):
    '''const_map_seq : const_map_item sep const_map_seq
                     | const_map_item const_map_seq
                     |'''
    _parse_seq(p)


def p_const_map_item(p):
    '''const_map_item : const_value ':' const_value'''
    p[0] = [p[1], p[3]]


def p_const_ref(p):
    '''const_ref : IDENTIFIER'''
    keys = p[1].split('.')

    if len(keys) == 1 and 'constants' in thrift \
            and keys[0] in thrift['constants']:
        p[0] = thrift['constants'][keys[0]]
        return
    elif len(keys) == 2 and 'ttypes' in thrift and \
        keys[0] in thrift['ttypes']:
        enum = thrift['ttypes'][keys[0]]
        if enum.ttype == 'enum' and keys[1] in enum:
            p[0] = enum[keys[1]]
            return
    raise ThriftGrammerError('No enum value or constant found named %r' % p[1])


def p_ttype(p):
    '''ttype : typedef
             | enum
             | struct
             | union
             | exception
             | service'''


def p_typedef(p):
    '''typedef : TYPEDEF definition_type IDENTIFIER'''
    thrift.setdefault('ttypes', {})[p[3]] = TTypeDef(type=p[2])


def p_enum(p):
    '''enum : ENUM IDENTIFIER '{' enum_seq '}' '''
    if not p[4]:
        thrift.setdefault('ttypes')[p[2]] = TEnum()
    else:
        init_val = p[4][0][1]
        vals = [-1 if init_val is None else init_val]

        for item in p[4]:
            if item[1] is None:
                val = vals[-1] + 1
                item[1] = val
                vals.append(val)
            vals.append(item[1])
        thrift.setdefault('ttypes', {})[p[2]] = TEnum(p[4])


def p_enum_seq(p):
    '''enum_seq : enum_item sep enum_seq
                | enum_item enum_seq
                |'''
    _parse_seq(p)


def p_enum_item(p):
    '''enum_item : IDENTIFIER '=' INTCONSTANT
                 | IDENTIFIER'''
    if len(p) == 4:
        p[0] = [p[1], p[3]]
    elif len(p) == 2:
        p[0] = [p[1], None]


def p_struct(p):
    '''struct : STRUCT IDENTIFIER '{' field_seq '}' '''
    thrift.setdefault('ttypes', {})[p[2]] = TStruct(p[4])


def p_union(p):
    '''union : UNION IDENTIFIER '{' field_seq '}' '''
    # thriftpy won't support union


def p_exception(p):
    '''exception : EXCEPTION IDENTIFIER '{' field_seq '}' '''
    thrift.setdefault('ttypes', {})[p[2]] = TException(p[4])


def p_service(p):
    '''service : SERVICE IDENTIFIER '{'  function_seq '}'
               | SERVICE IDENTIFIER EXTENDS IDENTIFIER '{' function_seq '}'
    '''
    if len(p) == 8:
        extends = p[4]
    elif len(p) == 6:
        extends = None

    thrift.setdefault('ttypes', {})[p[2]] = TService(functions=dict(p[len(p) - 2]),
                                                 extends=extends)


def p_function(p):
    '''function : ONEWAY function_type IDENTIFIER '(' field_seq ')' throws
                | ONEWAY function_type IDENTIFIER '(' field_seq ')'
                | function_type IDENTIFIER '(' field_seq ')' throws
                | function_type IDENTIFIER '(' field_seq ')' '''

    if p[1] == 'oneway':
        oneway = True
        base = 1
    else:
        oneway = False
        base = 0

    if p[len(p) - 1] == ')':
        throws = None
    else:
        throws = dict(p[len(p) - 1])

    p[0] = [p[base + 2], TFunction(oneway=oneway, throws=throws,
                                   type=p[base + 1], fields=dict(p[base + 4]))]


def p_function_seq(p):
    '''function_seq : function sep function_seq
                    | function function_seq
                    |'''
    _parse_seq(p)


def p_throws(p):
    '''throws : THROWS '(' field_seq ')' '''
    p[0] = dict(p[3])


def p_function_type(p):
    '''function_type : field_type
                     | VOID'''
    p[0] = p[1]


def p_field_seq(p):
    '''field_seq : field sep field_seq
                 | field field_seq
                 |'''
    _parse_seq(p)


def p_field(p):
    '''field : field_id field_req field_type IDENTIFIER
             | field_id field_req field_type IDENTIFIER '=' const_value'''
    p[0] = [p[4], TField(id=p[1], required=p[2], type=p[3], value=p[6]
                         if len(p) == 7 else None)]


def p_field_id(p):
    '''field_id : INTCONSTANT ':' '''
    p[0] = p[1]


def p_field_req(p):
    '''field_req : REQUIRED
                 | OPTIONAL
                 |'''
    if len(p) == 2:
        p[0] = p[1] == 'required'
    elif len(p) == 1:
        p[0] = True  # default: required=True


def p_field_type(p):
    '''field_type : IDENTIFIER
                  | definition_type'''
    p[0] = p[1]


def p_base_type(p):
    '''base_type : BOOL
                 | BYTE
                 | I16
                 | I32
                 | I64
                 | DOUBLE
                 | STRING
                 | BINARY'''
    p[0] = BASE_TYPE_MAPS[p[1]]()


def p_container_type(p):
    '''container_type : map_type
                      | list_type
                      | set_type'''
    p[0] = p[1]


def p_map_type(p):
    '''map_type : MAP '<' field_type ',' field_type '>' '''
    p[0] = TMap(['map', p[3], p[5]])


def p_list_type(p):
    '''list_type : LIST '<' field_type '>' '''
    p[0] = TList(['list', p[3]])


def p_set_type(p):
    '''set_type : SET '<' field_type '>' '''
    p[0] = TSet(['set', p[3]])


def p_definition_type(p):
    '''definition_type : base_type
                       | container_type'''
    p[0] = p[1]


parser = yacc.yacc(debug=False, write_tables=0)

thrift = None


def parse(data):
    global thrift
    thrift = {}
    lexer.lineno = 1
    parser.parse(data)
    return thrift


def _parse_seq(p):
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    elif len(p) == 3:
        p[0] = [p[1]] + p[2]
    elif len(p) == 1:
        p[0] = []
