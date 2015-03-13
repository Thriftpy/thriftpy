# -*- coding: utf-8 -*-

"""
IDL Ref:
    https://thrift.apache.org/docs/idl
"""

from __future__ import absolute_import

import os
from textwrap import TextWrapper, dedent
import types
from ply import lex, yacc
from .lexer import *  # noqa
from .exc import ThriftParserError, ThriftGrammerError
from ..thrift import gen_init, TType, TPayload, TException


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
                   | namespace
                   | doc'''


def p_include(p):
    '''include : INCLUDE LITERAL'''
    thrift = thrift_stack[-1]
    path = os.path.join(include_dir_, p[2])
    child = parse(path)
    setattr(thrift, child.__name__, child)


def p_namespace(p):
    '''namespace : NAMESPACE namespace_scope IDENTIFIER'''
    # namespace is useless in thriftpy
    # if p[2] == 'py' or p[2] == '*':
    #     setattr(thrift_stack[-1], '__name__', p[3])


def p_namespace_scope(p):
    '''namespace_scope : '*'
                       | IDENTIFIER'''
    p[0] = p[1]


def p_sep(p):
    '''sep : ','
           | ';'
    '''


def p_sep_optional(p):
    '''sep_optional : sep
                    | '''


def p_definition(p):
    '''definition : definition definition_unit_
                  |'''


def p_definition_unit_(p):
    '''definition_unit_ : definition_unit ';'
                        | definition_unit'''


def p_definition_unit(p):
    '''definition_unit : const
                       | ttype
                       | doc
    '''


def p_doc(p):
    '''doc : DOCTEXT doc
           | DOCTEXT '''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = p[1]


def p_const(p):
    '''const : doc iconst
             | iconst '''
    if len(p) == 3:
        doc = p[1]
        const = p[2]
    else:
        doc = None
        const = p[1]
    setattr(thrift_stack[-1], const[0], const[1])
    if doc is not None:
        const_doc = getattr(thrift_stack[-1], '_const_doc', None)
        if const_doc is None:
            const_doc = {}
            setattr(thrift_stack[-1], '_const_doc', const_doc)
        const_doc[const[0]] = doc


def p_iconst(p):
    '''iconst : CONST field_type IDENTIFIER '=' const_value sep_optional'''
    try:
        val = _cast(p[2])(p[5])
    except AssertionError:
        raise ThriftParserError('Type error for constant %s at line %d' %
                                (p[3], p.lineno(3)))
    p[0] = [p[3], val]


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
    '''const_list : '[' const_list_seq ']' '''
    p[0] = p[2]


def p_const_list_seq(p):
    '''const_list_seq : const_value sep_optional const_list_seq
                      |'''
    _parse_seq(p)


def p_const_map(p):
    '''const_map : '{' const_map_seq '}' '''
    p[0] = dict(p[2])


def p_const_map_seq(p):
    '''const_map_seq : const_map_item sep_optional const_map_seq
                     |'''
    _parse_seq(p)


def p_const_map_item(p):
    '''const_map_item : const_value ':' const_value '''
    p[0] = [p[1], p[3]]


def p_const_ref(p):
    '''const_ref : IDENTIFIER'''
    child = thrift_stack[-1]

    for name in p[1].split('.'):
        father = child
        child = getattr(child, name, None)
        if child is None:
            raise ThriftParserError('Cann\'t find name %r at line %d'
                                    % (p[1], p.lineno(1)))

    if _get_ttype(father) == TType.I32:
        # father is enum and child is its named value
        if child in father._named_values:
            p[0] = child
        else:
            raise ThriftParserError('No named enum value found named %r'
                                    % p[1])
    elif _get_ttype(child) is None:
        # child is a constant
        p[0] = child
    else:
        raise ThriftParserError('No named enum value or constant found '
                                'named %r' % p[1])


def p_ttype(p):
    '''ttype : typedef
             | enum
             | struct
             | union
             | exception
             | service'''


def p_typedef(p):
    '''typedef : doc itypedef
               | itypedef '''


def p_itypedef(p):
    '''itypedef : TYPEDEF field_type IDENTIFIER'''
    setattr(thrift_stack[-1], p[3], p[2])


def p_enum(p):
    '''enum : ienum
            | doc ienum '''
    if len(p) == 3:
        ienum = p[2]
        doctext = p[1]
    else:
        ienum = p[1]
        doctext = ''
    setattr(thrift_stack[-1], ienum[2], _make_enum(ienum[2], ienum[4], doctext=doctext))


def p_ienum(p):  # noqa
    '''ienum : ENUM IDENTIFIER '{' enum_seq '}' '''
    p[0] = [x.value for x in p.slice[0:]]


def p_enum_seq(p):
    '''enum_seq : enum_item sep_optional enum_seq
                |'''
    _parse_seq(p)


def p_enum_item(p):
    '''enum_item : ienum_item
                 | doc ienum_item '''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = p[1]


def p_ienum_item(p):
    '''ienum_item : IDENTIFIER '=' INTCONSTANT
                 | IDENTIFIER
                 |'''
    if len(p) == 4:
        p[0] = [p[1], p[3]]
    elif len(p) == 2:
        p[0] = [p[1], None]


def p_struct(p):
    '''struct : istruct
              | doc istruct '''

    if len(p) == 3:
        struct = p[2]
        doctext = p[1]
    else:
        struct = p[1]
        doctext = ''

    setattr(thrift_stack[-1], struct[2], _make_struct(struct[2], struct[4], doctext=doctext))


def p_istruct(p):
    '''istruct : STRUCT IDENTIFIER '{' field_seq '}' '''
    p[0] = [x.value for x in p.slice[0:]]


def p_union(p):
    '''union : doc iunion
             | iunion '''
    if len(p) == 3:
        iunion = p[2]
        doctext = p[1]
    else:
        iunion = p[1]
        doctext = ''
    setattr(thrift_stack[-1], iunion[2], _make_struct(iunion[2], iunion[4], doctext=doctext))


def p_iunion(p):
    '''iunion : UNION IDENTIFIER '{' field_seq '}' '''
    p[0] = [x.value for x in p.slice[0:]]


def p_exception(p):
    '''exception : iexception
                 | doc iexception '''
    if len(p) == 3:
        exceptdef  = p[2]
        doctext = p[1]
    else:
        exceptdef  = p[1]
        doctext = ''

    setattr(thrift_stack[-1], exceptdef[0], _make_struct(exceptdef[0], exceptdef[1],
                                                 base_cls=TException, doctext=doctext))

def p_iexception(p):
    '''iexception : EXCEPTION IDENTIFIER '{' field_seq '}' '''
    p[0] = [p[2], p[4]]


def p_service(p):
    '''service : doc iservice
               | iservice '''
    thrift = thrift_stack[-1]

    if len(p) == 3:
        doc = p[1]
        svc = p[2]
    else:
        doc = ''
        svc = p[1]

    if len(svc) == 8:
        extends = thrift
        for name in svc[4].split('.'):
            extends = getattr(extends, name, None)
            if extends is None:
                raise ThriftParserError('Can\'t find service %r for '
                                        'service %r to extend' %
                                        (svc[4], svc[2]))

        if not hasattr(extends, 'thrift_services'):
            raise ThriftParserError("Can't extends %r, not a service"
                                    % p[svc])

    else:
        extends = None

    setattr(thrift, svc[2], _make_service(svc[2], svc[len(svc) - 2], extends, docstring=doc))


def p_iservice(p):
    '''iservice : SERVICE IDENTIFIER '{' function_seq '}'
               | SERVICE IDENTIFIER EXTENDS IDENTIFIER '{' function_seq '}'
    '''
    p[0] = [x.value for x in p.slice[0:]]


def p_function(p):
    '''function : doc ifunction
                | ifunction '''
    if len(p) == 3:
        ifunction = p[2]
        doc = p[1]
    else:
        ifunction = p[1]
        doc = ''
    ifunction.append(doc)
    p[0] = ifunction



def p_ifunction(p):
    '''ifunction : ONEWAY function_type IDENTIFIER '(' field_seq ')' throws
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
        throws = []
    else:
        throws = p[len(p) - 1]

    p[0] = [oneway, p[base + 1], p[base + 2], p[base + 4], throws]


def p_function_seq(p):
    '''function_seq : function sep_optional function_seq
                    | function_seq
                    | doc
                    | function_seq doc
                    |'''
    if (len(p) == 2) and (p.slice[1].type == 'doc'):
        p[0] = [p[0]]
    else:
        # Rule to deal with trailing doc
        if (len(p) == 3) and (p.slice[2].type == 'doc'):
            _parse_seq(p[:2])
        else:
            _parse_seq(p)


def p_throws(p):
    '''throws : THROWS '(' field_seq ')' '''
    p[0] = p[3]


def p_function_type(p):
    '''function_type : field_type
                     | VOID'''
    if p[1] == 'void':
        p[0] = TType.VOID
    else:
        p[0] = p[1]


def p_field_seq(p):
    '''field_seq : field sep_optional field_seq
                 | doc
                 | field_seq doc
                 | '''
    if (len(p) == 2) and (p.slice[1].type == 'doc'):
        p[0] = [p[0]]
    else:
        # Rule to deal with trailing doc
        if (len(p) == 3) and (p.slice[2].type == 'doc'):
            _parse_seq(p[:2])
        else:
            _parse_seq(p)


def p_field(p):
    '''field : doc ifield
             | ifield '''
    if len(p) == 3:
        doctext = p[1]
        ifield = p[2]
    else:
        doctext = ''
        ifield = p[1]
    ifield.append(doctext)
    p[0] = ifield


def p_ifield(p):
    '''ifield : field_id field_req field_type IDENTIFIER
             | field_id field_req field_type IDENTIFIER '=' const_value
             '''

    if len(p) == 7:
        try:
            val = _cast(p[3])(p[6])
        except AssertionError:
            raise ThriftParserError(
                'Type error for field %s '
                'at line %d' % (p[4], p.lineno(4)))
    else:
        val = None

    p[0] = [p[1], p[2], p[3], p[4], val]


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
        p[0] = False  # default: required=False


def p_field_type(p):
    '''field_type : ref_type
                  | definition_type'''
    p[0] = p[1]


def p_ref_type(p):
    '''ref_type : IDENTIFIER'''
    ref_type = thrift_stack[-1]

    for name in p[1].split('.'):
        ref_type = getattr(ref_type, name, None)
        if ref_type is None:
            raise ThriftParserError('No type found: %r, at line %d' %
                                    (p[1], p.lineno(1)))

    if hasattr(ref_type, '_ttype'):
        p[0] = getattr(ref_type, '_ttype'), ref_type
    else:
        p[0] = ref_type


def p_base_type(p):  # noqa
    '''base_type : BOOL
                 | BYTE
                 | I16
                 | I32
                 | I64
                 | DOUBLE
                 | STRING
                 | BINARY'''
    if p[1] == 'bool':
        p[0] = TType.BOOL
    if p[1] == 'byte':
        p[0] = TType.BYTE
    if p[1] == 'i16':
        p[0] = TType.I16
    if p[1] == 'i32':
        p[0] = TType.I32
    if p[1] == 'i64':
        p[0] = TType.I64
    if p[1] == 'double':
        p[0] = TType.DOUBLE
    if p[1] == 'string':
        p[0] = TType.STRING
    if p[1] == 'binary':
        p[0] = TType.BINARY


def p_container_type(p):
    '''container_type : map_type
                      | list_type
                      | set_type'''
    p[0] = p[1]


def p_map_type(p):
    '''map_type : MAP '<' field_type ',' field_type '>' '''
    p[0] = TType.MAP, (p[3], p[5])


def p_list_type(p):
    '''list_type : LIST '<' field_type '>' '''
    p[0] = TType.LIST, p[3]


def p_set_type(p):
    '''set_type : SET '<' field_type '>' '''
    p[0] = TType.SET, p[3]


def p_definition_type(p):
    '''definition_type : base_type
                       | container_type'''
    p[0] = p[1]


thrift_stack = []
include_dir_ = '.'
thrift_cache = {}


def parse(path, module_name=None, include_dir=None,
          lexer=None, parser=None, enable_cache=True):

    # dead include checking on current stack
    for thrift in thrift_stack:
        if os.path.samefile(path, thrift.__thrift_file__):
            raise ThriftParserError('Dead including on %s' % path)

    global thrift_cache

    cache_key = module_name or os.path.normpath(path)

    if enable_cache and cache_key in thrift_cache:
        return thrift_cache[cache_key]

    if lexer is None:
        lexer = lex.lex()
    if parser is None:
        parser = yacc.yacc(debug=False, write_tables=0)

    global include_dir_

    if include_dir is not None:
        include_dir_ = include_dir

    if not path.endswith('.thrift'):
        raise ThriftParserError('Path should end with .thrift')

    with open(path) as fh:
        data = fh.read()

    if module_name is not None and not module_name.endswith('_thrift'):
        raise ThriftParserError('ThriftPy can only generate module with '
                                '\'_thrift\' suffix')

    if module_name is None:
        basename = os.path.basename(path)
        module_name = os.path.splitext(basename)[0]

    thrift = types.ModuleType(module_name)
    setattr(thrift, '__thrift_file__', path)
    thrift_stack.append(thrift)
    lexer.lineno = 1
    parser.parse(data)
    thrift_stack.pop()

    if enable_cache:
        thrift_cache[cache_key] = thrift
    return thrift


def _parse_seq(p):
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    elif len(p) == 3:
        p[0] = [p[1]] + p[2]
    elif len(p) == 1:
        p[0] = []


def _cast(t):  # noqa
    if t == TType.BOOL:
        return _cast_bool
    if t == TType.BYTE:
        return _cast_byte
    if t == TType.I16:
        return _cast_i16
    if t == TType.I32:
        return _cast_i32
    if t == TType.I64:
        return _cast_i64
    if t == TType.DOUBLE:
        return _cast_double
    if t == TType.STRING:
        return _cast_string
    if t == TType.BINARY:
        return _cast_binary
    if t[0] == TType.LIST:
        return _cast_list(t)
    if t[0] == TType.SET:
        return _cast_set(t)
    if t[0] == TType.MAP:
        return _cast_map(t)
    if t[0] == TType.I32:
        return _cast_enum(t)
    if t[0] == TType.STRUCT:
        return _cast_struct(t)


def _cast_bool(v):
    assert isinstance(v, bool)
    return v


def _cast_byte(v):
    assert isinstance(v, str)
    return v


def _cast_i16(v):
    assert isinstance(v, int)
    return v


def _cast_i32(v):
    assert isinstance(v, int)
    return v


def _cast_i64(v):
    assert isinstance(v, int)
    return v


def _cast_double(v):
    assert isinstance(v, float)
    return v


def _cast_string(v):
    assert isinstance(v, str)
    return v


def _cast_binary(v):
    assert isinstance(v, str)
    return v


def _cast_list(t):
    assert t[0] == TType.LIST

    def __cast_list(v):
        assert isinstance(v, list)
        map(_cast(t[1]), v)
        return v
    return __cast_list


def _cast_set(t):
    assert t[0] == TType.SET

    def __cast_set(v):
        assert isinstance(v, (list, set))
        map(_cast(t[1]), v)
        if not isinstance(v, set):
            return set(v)
        return v
    return __cast_set


def _cast_map(t):
    assert t[0] == TType.MAP

    def __cast_map(v):
        assert isinstance(v, dict)
        for key in v:
            v[_cast(t[1][0])(key)] = \
                _cast(t[1][1])(v[key])
        return v
    return __cast_map


def _cast_enum(t):
    assert t[0] == TType.I32

    def __cast_enum(v):
        assert isinstance(v, int)
        if v in getattr(t[1], '_named_values'):
            return v
        raise ThriftParserError('Couldn\'t find a named value in enum '
                                '%s for value %d' % (t[1].__name__, v))
    return __cast_enum


def _cast_struct(t):   # struct/exception/union
    assert t[0] == TType.STRUCT

    def __cast_struct(v):
        if isinstance(v, t[1]):
            return v  # already cast

        assert isinstance(v, dict)
        tspec = getattr(t[1], '_tspec')

        for key in tspec:  # requirement check
            if tspec[key][0] and key not in v:
                raise ThriftParserError('Field %r was required to create '
                                        'constant for type %r' %
                                        (key, t[1].__name__))

        for key in v:  # cast values
            if key not in tspec:
                raise ThriftParserError('No field named %r was '
                                        'found in struct of type %r' %
                                        (key, t[1].__name__))
            v[key] = _cast(tspec[key][1])(v[key])
        return t[1](**v)
    return __cast_struct


def _make_enum(name, kvs, doctext=''):
    attrs = {'__module__': thrift_stack[-1].__name__, '_ttype': TType.I32, '__doc__': doctext}
    cls = type(name, (object, ), attrs)
    named_values = set()
    for key, val in kvs:
        if val is not None:
            named_values.add(val)
    setattr(cls, '_named_values', named_values)

    _values_to_names = {}
    _names_to_values = {}

    if kvs:
        val = kvs[0][1]
        if val is None:
            val = -1
        for item in kvs:
            if item[1] is None:
                item[1] = val + 1
            val = item[1]
        for key, val in kvs:
            setattr(cls, key, val)
            _values_to_names[val] = key
            _names_to_values[key] = val
    setattr(cls, '_VALUES_TO_NAMES', _values_to_names)
    setattr(cls, '_NAMES_TO_VALUES', _names_to_values)
    return cls


def _get_container_elem_typename(container_spec):
    if isinstance(container_spec, tuple):
        v_type, v_spec = container_spec[0], container_spec[1]
    else:
        v_type, v_spec = container_spec, None

    return _get_type_name((v_type, '', v_spec, True))


def _get_type_name(thrift_spec):

    if len(thrift_spec) == 3:
        sf_type, f_name, f_req = thrift_spec
        f_container_spec = None
    else:
        sf_type, f_name, f_container_spec, f_req = thrift_spec

    if sf_type == TType.STRUCT:
        return str(f_container_spec)
    elif (sf_type < TType.STRUCT) or (sf_type == TType.UTF8) or (sf_type == TType.UTF16):
        # Primitive
        return str(TType._VALUES_TO_NAMES[sf_type]).capitalize()
    else:
        # Complex type
        container_name = TType._VALUES_TO_NAMES[sf_type].capitalize()
        if (sf_type == TType.LIST) or (sf_type == TType.SET):
            elem_name = _get_container_elem_typename(f_container_spec)
        elif sf_type == TType.MAP:
            k_name = _get_container_elem_typename(f_container_spec[0])
            v_name = _get_container_elem_typename(f_container_spec[0])
            elem_name = '{}, {}'.format(k_name, v_name)
        else:
            raise ThriftParserError("Unexpected container type %s" % sf_type)
        return '{}<{}>'.format(container_name, elem_name)


def _doc_text_chunk(doc):
    out = []
    for elem in doc.split('\n'):
        if elem:
            out.append(elem)
        else:
            yield '\n'.join(out)
            out = []
    if len(out):
        yield '\n'.join(out)


def _doc_reformat_par(doc, tw):
    for c in _doc_text_chunk(doc):
        yield '\n'.join(tw.wrap(c))


def _docstring_reformat(doc, tw):
    return '\n\n'.join(list(_doc_reformat_par(doc, tw)))


def _make_field_docstring(field, tw=TextWrapper(initial_indent=' '*4, subsequent_indent=' '*4, width=110)):
    name = field[3]
    ttype = field[2]
    typespec = _ttype_spec(ttype, field[3], field[1])

    type_string = _get_type_name(typespec)

    if len(field) == 6:
        _field_doc = field[5]
    else:
        _field_doc = ''
    doc = name + ' : ' + type_string + '\n' + _docstring_reformat(_field_doc, tw)
    return doc.rstrip()


def _make_struct(name, fields, ttype=TType.STRUCT, base_cls=TPayload,
                 _gen_init=True, doctext='', field_header='Parameters'):
    attrs = {'__module__': thrift_stack[-1].__name__, '_ttype': ttype}
    cls = type(name, (base_cls, ), attrs)
    thrift_spec = {}
    default_spec = []
    _tspec = {}
    _doc = []

    for field in fields:
        if field is None:
            continue
        ttype = field[2]
        thrift_spec[field[0]] = _ttype_spec(ttype, field[3], field[1])
        default_spec.append((field[3], field[4]))
        _tspec[field[3]] = field[1], ttype
        _doc.append(_make_field_docstring(field))

    #TODO : Append doctext for class memnbers

    setattr(cls, 'thrift_spec', thrift_spec)
    setattr(cls, 'default_spec', default_spec)
    setattr(cls, '_tspec', _tspec)

    if len(_doc):
        doctext += dedent('''

            {field_header}
            {line}
            '''.format(field_header=field_header, line='-'* len(field_header))) + '\n'.join(_doc)

    setattr(cls, '__doc__', doctext)
    if _gen_init:
        gen_init(cls, thrift_spec, default_spec)
    return cls


def _make_service(name, funcs, extends, docstring=''):
    if (extends is not None) and (not docstring):
        docstring = extends.__doc__

    if extends is None:
        extends = object

    attrs = {'__module__': thrift_stack[-1].__name__, '__doc__': docstring}
    cls = type(name, (extends, ), attrs)
    thrift_services = []
    thrift_services_doc = {}

    for func in funcs:
        if func is None:
            continue
        func_name = func[2]
        # args payload cls
        args_name = '%s_args' % func_name
        args_fields = func[3]
        #print(func)
        doctext = func[5] if len(func) == 6 else ''
        args_cls = _make_struct(args_name, args_fields, doctext=doctext)
        setattr(cls, args_name, args_cls)
        # result payload cls
        result_name = '%s_result' % func_name
        result_type = func[1]
        result_throws = func[4]
        result_oneway = func[0]
        result_cls = _make_struct(result_name, result_throws, _gen_init=False, field_header='Raises')
        setattr(result_cls, 'oneway', result_oneway)
        if result_type != TType.VOID:
            result_cls.thrift_spec[0] = _ttype_spec(result_type, 'success')
            result_cls.default_spec.insert(0, ('success', None))
            result_type_docstring = dedent('''
             Returns
             -------
             success : ''' + _get_type_name(result_cls.thrift_spec[0]))
        else:
            result_type_docstring = ''

        function_docstring = '\n\n'.join(x.strip() for x in (args_cls.__doc__, result_cls.__doc__, result_type_docstring) if x)

        gen_init(result_cls, result_cls.thrift_spec, result_cls.default_spec)
        setattr(cls, result_name, result_cls)
        thrift_services.append(func_name)
        thrift_services_doc[func_name] = function_docstring
    if extends is not None and hasattr(extends, 'thrift_services'):
        thrift_services.extend(extends.thrift_services)
    if extends is not None and hasattr(extends, 'thrift_services_doc'):
        thrift_services_doc.update(extends.thrift_services_doc)
    setattr(cls, 'thrift_services', thrift_services)
    setattr(cls, 'thrift_services_doc', thrift_services_doc)
    return cls


def _ttype_spec(ttype, name, required=False):
    if isinstance(ttype, int):
        return ttype, name, required
    else:
        return ttype[0], name, ttype[1], required


def _get_ttype(inst, default_ttype=None):
    if hasattr(inst, '__dict__') and '_ttype' in inst.__dict__:
        return inst.__dict__['_ttype']
    return default_ttype
