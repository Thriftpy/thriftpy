# -*- coding: utf-8 -*-

"""
IDL Ref:
    https://thrift.apache.org/docs/idl
"""

from __future__ import absolute_import

import collections
import os
import sys
import types
import re
import parsley
from .exc import ThriftParserError, ThriftGrammerError
from thriftpy._compat import urlopen, urlparse
from ..thrift import gen_init, TType, TPayload, TException


class ModuleLoader(object):
    '''
    Primary API for loading thrift files as modules.
    '''
    def __init__(self, include_dirs=('.',)):
        self.modules = {}
        self.samefile = getattr(os.path,'samefile', lambda f1, f2: os.stat(f1) == os.stat(f2))
        self.include_dirs = include_dirs

    def load(self, path, module_name):
        return self._load(
            path, True, path, module_name=module_name)

    def load_data(self, data, module_name, load_includes=False, path=None):
        return self._load_data(
            data, module_name, load_includes=load_includes, abs_path=os.path.abspath(path))

    def _load(self, path, load_includes, parent_path, sofar=(), module_name=None):
        if not path.endswith('.thrift'):
            raise ParseError()  # ...
        if os.path.isabs(path):
            abs_path = path
        else:
            parent_dir = os.path.dirname(parent_path) or '.'  # prevent empty path from turning into '/'
            for base in [parent_dir] + list(self.include_dirs):
                abs_path = base + '/' + path
                if os.path.exists(abs_path):
                    abs_path = os.path.abspath(abs_path)
                    break
            else:
                raise ParseError('could not find import {0} (from {1})'.format(path, parent_path))
        if abs_path in sofar:
            cycle = sofar[sofar.index(abs_path):] + (abs_path,)
            path_to_cycle = sofar[:sofar.index(abs_path)]
            msg = 'circular import:\n{0}'.format(' ->\n'.join(cycle))
            if path_to_cycle:
                msg += "\nvia:\n{0}".format(' ->\n'.join(path_to_cycle))
            raise CircularInclude(msg)
        with open(abs_path, 'rb') as f:
            data = f.read()
        if module_name is None:
            module_name = os.path.splitext(os.path.basename(abs_path))[0]  # remove '.thrift' from end
        return self._load_data(
            data, module_name, load_includes, abs_path, sofar + (abs_path,))

    def _cant_load(self, path, *a, **kw):
        raise ThriftParserError('unexpected include statement while loading from data')

    def _load_data(self, data, module_name, load_includes, abs_path, sofar=()):
        cache_key = (module_name, abs_path)
        if cache_key in self.modules:
            return self.modules[cache_key]
        module = types.ModuleType(module_name)
        module.__thrift_file__ = abs_path
        module.__thrift_meta__ = collections.defaultdict(list)
        try:
            if not load_includes:
                document = PARSER(data).Document(module, self._cant_load)
            else:
                # path = path of file to be loaded
                # abs_path = path of parent file to enable relative imports
                document = PARSER(data).Document(
                    module, lambda path: self._load(path, load_includes, abs_path, sofar))
        except parsley.ParseError as pe:
            raise ThriftParserError(
                str(pe) + '\n in module {0} from {1}'.format(module_name, abs_path))
        self.modules[cache_key] = module
        return self.modules[cache_key]


class CircularInclude(ThriftParserError, ImportError): pass


MODULE_LOADER = ModuleLoader()


def parse(path, module_name=None, include_dirs=None, include_dir=None,
          enable_cache=True):
    """Parse a single thrift file to module object, e.g.::

        >>> from thriftpy.parser.parser import parse
        >>> note_thrift = parse("path/to/note.thrift")
        <module 'note_thrift' (built-in)>

    :param path: file path to parse, should be a string ending with '.thrift'.
    :param module_name: the name for parsed module, the default is the basename
                        without extension of `path`.
    :param include_dirs: directories to find thrift files while processing
                         the `include` directive, by default: ['.'].
    :param include_dir: directory to find child thrift files. Note this keyword
                        parameter will be deprecated in the future, it exists
                        for compatiable reason. If it's provided (not `None`),
                        it will be appended to `include_dirs`.
    :param enable_cache: if this is set to be `True`, parsed module will be
                         cached, this is enabled by default. If `module_name`
                         is provided, use it as cache key, else use the `path`.
    """
    if enable_cache and module_name in MODULE_LOADER.modules:
        return MODULE_LOADER.modules[module_name]

    cache_key = module_name or os.path.normpath(path)

    if include_dirs is not None:
        MODULE_LOADER.include_dirs = include_dirs
    if include_dir is not None:
        MODULE_LOADER.include_dirs.append(include_dir)

    if not path.endswith('.thrift'):
        raise ThriftParserError('Path should end with .thrift')

    url_scheme = urlparse(path).scheme
    if url_scheme == 'file':
        path = urlparse(path).netloc + urlparse(path).path
        with open(path) as fh:
            data = fh.read()
    elif url_scheme == '':
        with open(path) as fh:
            data = fh.read()
    elif url_scheme in ('http', 'https'):
        data = urlopen(path).read()
        return MODULE_LOADER.load_data(data, module_name, False)
    else:
        raise ThriftParserError('ThriftPy does not support generating module '
                                'with path in protocol \'{0}\''.format(
                                    url_scheme))

    if module_name is not None and not module_name.endswith('_thrift'):
        raise ThriftParserError('ThriftPy can only generate module with '
                                '\'_thrift\' suffix')

    if module_name is None:
        basename = os.path.basename(path)
        module_name = os.path.splitext(basename)[0]

    module = MODULE_LOADER.load_data(data, module_name, True, path)
    if not enable_cache:
        del MODULE_LOADER.modules[module_name]
    return module


def parse_fp(source, module_name, enable_cache=True):
    """Parse a file-like object to thrift module object, e.g.::

        >>> from thriftpy.parser.parser import parse_fp
        >>> with open("path/to/note.thrift") as fp:
                parse_fp(fp, "note_thrift")
        <module 'note_thrift' (built-in)>

    :param source: file-like object, expected to have a method named `read`.
    :param module_name: the name for parsed module, shoule be endswith
                        '_thrift'.
    :param enable_cache: if this is set to be `True`, parsed module will be
                         cached by `module_name`, this is enabled by default.
    """
    if not module_name.endswith('_thrift'):
        raise ThriftParserError('ThriftPy can only generate module with '
                                '\'_thrift\' suffix')

    if enable_cache and module_name in MODULE_LOADER.modules:
        return MODULE_LOADER.modules[module_name]

    if not hasattr(source, 'read'):
        raise ThriftParserError('Except `source` to be a file-like object with'
                                'a method named \'read\'')

    if enable_cache:
        module = MODULE_LOADER.load_data(source.read(), module_name, False, '<string>/' + module_name)
    else:  # throw-away isolated ModuleLoader instance
        return ModuleLoader().load_data(source.read(), module_name, False, '<string>/' + module_name)

    module.__thrift_file__ = None

    return module


def _cast_struct(t, v):   # struct/exception/union
    tspec = getattr(t[1], '_tspec')

    for key in tspec:  # requirement check
        if tspec[key][0] and key not in v:
            raise ThriftParserError('Field %r was required to create '
                                    'constant for type %r' %
                                    (key, t[1].__name__))

    for key in v:  # extra values check
        if key not in tspec:
            raise ThriftParserError('No field named %r was '
                                    'found in struct of type %r' %
                                    (key, t[1].__name__))
    return t[1](**v)


def _make_enum(name, kvs, module):
    attrs = {'__module__': module.__name__, '_ttype': TType.I32}
    cls = type(name, (object, ), attrs)

    _values_to_names = {}
    _names_to_values = {}

    if kvs:
        val = kvs[0][1]
        if val is None:
            val = -1
        for item in kvs:
            if item[1] is None:
                val = val + 1
            else:
                val = item[1]
            key = item[0]
            setattr(cls, key, val)
            _values_to_names[val] = key
            _names_to_values[key] = val
    cls._VALUES_TO_NAMES = _values_to_names
    cls._NAMES_TO_VALUES = _names_to_values
    return cls


def _make_empty_struct(name, module, ttype=TType.STRUCT, base_cls=TPayload, docstring=''):
    attrs = {'__module__': module.__name__, '_ttype': ttype, '__doc__': docstring}
    module.__dict__[name] = type(name, (base_cls, ), attrs)
    return module.__dict__[name]


def _fill_in_struct(cls, fields, _gen_init=True):
    thrift_spec = {}
    default_spec = []
    _tspec = {}

    for field in fields:
        if field.id in thrift_spec or field.name in _tspec:
            raise ThriftGrammerError(('\'%d:%s\' field identifier/name has '
                                      'already been used') % (field.id,
                                                              field.name))
        thrift_spec[field.id] = _ttype_spec(field.ttype, field.name, field.req)
        default_spec.append((field.name, field.default))
        _tspec[field.name] = field.req == 'required', field.ttype
    cls.thrift_spec = thrift_spec
    cls.default_spec = default_spec
    cls._tspec = _tspec
    if _gen_init:
        gen_init(cls, thrift_spec, default_spec)
    return cls


def _make_struct(name, fields, module, ttype=TType.STRUCT, base_cls=TPayload,
                 _gen_init=True, docstring=''):
    cls = _make_empty_struct(name, module, ttype=ttype, base_cls=base_cls, docstring=docstring)
    return _fill_in_struct(cls, fields or (), _gen_init=_gen_init)


def _make_service(name, funcs, extends, module, docstring):
    if extends is None:
        extends = object

    attrs = {'__module__': module.__name__, '__doc__': docstring}
    cls = type(name, (extends, ), attrs)
    thrift_services = []

    for func in funcs:
        # args payload cls
        args_name = '%s_args' % func.name
        args_fields = func.fields
        args_cls = _make_struct(args_name, args_fields, module, docstring=func.docstring)
        setattr(cls, args_name, args_cls)
        # result payload cls
        result_name = '%s_result' % func.name
        result_cls = _make_struct(result_name, func.throws, module,
                                  _gen_init=False)
        setattr(result_cls, 'oneway', func.oneway)
        if func.ttype != TType.VOID:
            result_cls.thrift_spec[0] = _ttype_spec(func.ttype, 'success')
            result_cls.default_spec.insert(0, ('success', None))
        gen_init(result_cls, result_cls.thrift_spec, result_cls.default_spec)
        setattr(cls, result_name, result_cls)
        thrift_services.append(func.name)
    if extends is not None and hasattr(extends, 'thrift_services'):
        thrift_services.extend(extends.thrift_services)
    cls.thrift_services = thrift_services
    cls.thrift_extends = extends
    return cls


def _ttype_spec(ttype, name, required=False):
    if required is not False:
        required = (required == 'required')  # 'default' counts as 'optional'
    if isinstance(ttype, int):
        return ttype, name, required
    else:
        return ttype[0], name, ttype[1], required


def _get_ttype(inst, default_ttype=None):
    if hasattr(inst, '__dict__') and '_ttype' in inst.__dict__:
        return inst.__dict__['_ttype']
    return default_ttype


def _make_exception(name, fields, module):
    return _make_struct(name, fields, module, base_cls=TException)


def _make_const(name, val, ttype):
    return 'const', name, val, _cast(ttype)(val)


def _add_definition(module, type, name, val, ttype):
    module.__thrift_meta__[type + 's'].append(val)
    setattr(module, name, val)
    # TODO: this seems crazy
    if hasattr(val, '_NAMES_TO_VALUES'):
        module.__dict__.update(val._NAMES_TO_VALUES)
    return type, name, val, ttype


def _add_include(module, path, loadf):
    included = loadf(path)
    module.__dict__[included.__name__] = included
    module.__thrift_meta__['includes'].append(included)
    return 'include', included


def _lookup_symbol(module, identifier):
    names = identifier.split('.')
    def lookup_from(val, names):
        for name in names:
            val = getattr(val, name)
        return val
    try:
        return lookup_from(module, names)
    except AttributeError:  # TODO: a cleaner way to handle multiple includes with same name?
        mod_name, rest = names[0], names[1:]
        for included in module.__thrift_meta__['includes']:
            if mod_name == included.__name__:
                try:
                    return lookup_from(included, rest)
                except AttributeError:
                    pass
        raise UnresovledReferenceError(
            'could not resolve name {0} in module {1} (from {2})'.format(
                identifier, module.__name__, module.__thrift_file__))


class UnresovledReferenceError(ThriftParserError): pass


def _ref_type(module, name):
    'resolve a reference to a type, return the resulting ttype'
    val = _lookup_symbol(module, name)
    if val in BASE_TYPE_MAP.values():
        return val
    if isinstance(val, tuple):  # typedef
        return val
    return val._ttype, val  # struct or enum


def _ref_val(module, name):
    'resolve a reference to a value, return the value'
    val = _lookup_symbol(module, name)
    if isinstance(val, type):
        raise UnresovledReferenceError("{0} in {1} is a type, not a value".format(name, module))
    return val


class NoSuchAttribute(ThriftParserError): pass


def _attr_ttype(struct, attr):
    'return the ttype of attr in struct'
    if attr not in struct._tspec:
        raise NoSuchAttribute('no attribute {0} of struct {1} in module {2}'.format(
            attr, struct.__name__, struct.__module__))
    return struct._tspec[attr][1]


GRAMMAR = '''
Document :module :load_module = (brk Header(module load_module))*:hs (brk Definition(module))*:ds brk -> Document(hs, ds)
Header :module :load_module = <Include(module load_module) | Namespace>
Include :module :load_module = brk 'include' brk Literal:path ListSeparator? -> Include(module, path, load_module)
Namespace =\
    brk 'namespace' brk <((NamespaceScope ('.' Identifier)?)| unsupported_namespacescope)>:scope brk\
        Identifier:name brk uri? -> 'namespace', scope, name
uri = '(' ws 'uri' ws '=' ws Literal:uri ws ')' -> uri
NamespaceScope = ('*' | 'cpp' | 'java' | 'py.twisted' | 'py' | 'perl' | 'rb' | 'cocoa' | 'csharp' |
                  'xsd' | 'c_glib' | 'js' | 'st' | 'go' | 'php' | 'delphi' | 'lua')
unsupported_namespacescope = Identifier
Definition :module = brk (Const(module) | Typedef(module) | Enum(module) | Struct(module) | Union(module) |
                           Exception(module) | Service(module)):defn -> Definition(module, *defn)
Const :module = 'const' brk FieldType(module):ttype brk Identifier:name brk '='\
    brk ConstValue(module ttype):val brk ListSeparator? -> 'const', name, val, ttype
Typedef :module = 'typedef' brk DefinitionType(module):type brk annotations brk Identifier:alias brk annotations\
                   -> 'typedef', alias, type, None
Enum :module = 'enum' brk Identifier:name brk '{' enum_item*:vals '}' brk annotations brk\
                -> 'enum', name, Enum(name, vals, module), None
# enum items are always referenced with the enum name as a prefix, so are never ambiguous
# with language keywords; any token is okay not just valid identifiers
enum_item = brk token:name brk ('=' brk int_val)?:value brk annotations ListSeparator? brk -> name, value
Struct :module = 'struct' brk DeclareStruct(module):cls brk fields(module):fields brk immutable?\
                 -> 'struct', cls.__name__, _fill_in_struct(cls, fields), None
Union :module = 'union' brk DeclareStruct(module):cls brk fields(module):fields\
                 -> 'union', cls.__name__, _fill_in_struct(cls, fields), None
Exception :module = 'exception' brk Identifier:name brk fields(module):fields\
                     -> 'exception', name, Exception_(name, fields, module), None
DeclareStruct :module = Identifier:name !(DeclareStruct(name, module))
fields :module = '{' (brk Field(module))*:fields brk '}' brk annotations brk -> fields
Service :module =\
    'service' brk Identifier:name (brk 'extends' brk identifier_ref(module))?:extends docstring:docstring\
        '{' (brk Function(module))*:funcs brk annotations brk '}' brk annotations brk\
    -> 'service', name, Service(name, funcs, extends, module, docstring), None
Field :module = brk FieldID:id brk FieldReq?:req brk FieldType(module):ttype brk Identifier:name brk\
    ('=' brk ConstValue(module ttype))?:default brk annotations brk ListSeparator? -> Field(id, req, ttype, name, default)
FieldID = int_val:val ':' -> val
FieldReq = 'required' | 'optional' | !(b'default')
# Functions
Function :module = 'oneway'?:oneway brk FunctionType(module):ft brk Identifier:name brk '(' (brk Field(module)*):fs brk ')'\
     (brk Throws(module))?:throws (brk ListSeparator)? docstring:docstring -> Function(name, ft, fs, oneway, throws, docstring)
FunctionType :module = ('void' !(TType.VOID)) | FieldType(module)
Throws :module = 'throws' brk '(' (brk Field(module))*:fs ')' -> fs
# Types
FieldType :module = (ContainerType(module) | BaseType | RefType(module)):ttype brk annotations brk -> ttype
DefinitionType :module = BaseType | ContainerType(module)
BaseType = ('bool' | 'byte' | 'i8' | 'i16' | 'i32' | 'i64' | 'double' | 'string' | 'binary'):ttype\
           -> BaseTType(ttype)
ContainerType :module = (MapType(module) | SetType(module) | ListType(module)):type brk immutable? -> type
MapType :module = 'map' CppType? brk '<' brk FieldType(module):keyt brk ',' brk FieldType(module):valt brk '>' -> TType.MAP, (keyt, valt)
SetType :module = 'set' CppType? brk '<' brk FieldType(module):valt brk '>' -> TType.SET, valt
ListType :module = 'list' brk '<' brk FieldType(module):valt brk '>' brk CppType? -> TType.LIST, valt
RefType :module = Identifier:name !(_ref_type(module, name))
RefVal :module = Identifier:name !(_ref_val(module, name))
CppType = 'cpp_type' Literal -> None
# Constant Values
ConstValue :module :ttype = DoubleConstant(ttype) | BoolConstant(ttype) | IntConstant(ttype) | ConstList(module ttype)\
                            | ConstSet(module ttype) | ConstMap(module ttype) | ConstStruct(module ttype)\
                            | EnumConstant(ttype) | ConstLiteral(ttype) | RefVal(module)
int_val = <('+' | '-')? digit+>:val -> int(val)
IntConstant :ttype = ?(ttype in (TType.BYTE, TType.I16, TType.I32, TType.I64)) int_val
EnumConstant :ttype = check_ttype(TType.I32 ttype)\
                      (int_val:val ?(val in ttype[1]._VALUES_TO_NAMES) -> val) | \
                      (token:val ?(type(ttype) is tuple and val in getattr(ttype[1], "_NAMES_TO_VALUES", ())) -> ttype[1]._NAMES_TO_VALUES[val])
DoubleConstant :ttype = ?(ttype == TType.DOUBLE) <('+' | '-')? (digit* '.' digit+) | digit+ (('E' | 'e') int_val)?>:val\
                 -> float(val)
BoolConstant :ttype = ?(ttype == TType.BOOL) \
                      ((('true' | 'false'):val -> val == 'true') | (int_val:val -> bool(val)))
ConstLiteral :ttype = ?(ttype in (TType.STRING, TType.BINARY)) Literal
ConstList :module :ttype = check_ttype(TType.LIST ttype) array_vals(module ttype[1])
ConstSet :module :ttype = (check_ttype(TType.SET ttype) array_vals(module ttype[1]):vals -> set(vals)) | ('{}' -> set())
array_vals :module :ttype = '[' (brk ConstValue(module ttype):val ListSeparator? -> val)*:vals ']' -> vals
ConstMap :module :ttype = check_ttype(TType.MAP ttype)\
    '{' (brk ConstValue(module ttype[1][0]):key brk ':' \
        brk ConstValue(module ttype[1][1]):val ListSeparator? -> key, val)*:items brk '}' brk\
    -> dict(items)
ConstStruct :module :ttype = check_ttype(TType.STRUCT ttype) \
    '{' (brk Literal:name brk ':' brk !(_attr_ttype(ttype[1], name)):attr_ttype \
        ConstValue(module attr_ttype):val brk ListSeparator? brk -> name, val)*:items brk '}' brk\
    -> _cast_struct(ttype, dict(items))
check_ttype :match :ttype = ?(isinstance(ttype, tuple) and ttype[0] == match)
# Basic Definitions
Literal = str_val_a | str_val_b
# 2 levels of string interpolation = \\\\ to get slash literal
str_val_a = '"' <(('\\\\' '"') | (~'"' anything))*>:val '"' -> val
sq :c = ?("'" == c)
str_val_b = sq <(('\\\\' sq) | (~sq anything))*>:val sq -> val
token = <(letter | '_') (letter | digit | '.' | '_')*>
Identifier = token:val ?(not is_reserved(val))^(reserved keyword not valid in this context) -> val
identifier_ref :module = Identifier:val -> IdentifierRef(module, val)  # unresolved reference
annotations = (brk '(' annotation*:name_vals')' brk -> name_vals)? | !(())  # always optional
annotation = brk Identifier:name brk ('=' brk Literal)?:val brk ListSeparator? brk -> name, val
ListSeparator = ',' | ';'
Comment = cpp_comment | c_comment | python_comment
brk = (white | c_comment | cpp_comment | python_comment)*
white = <' ' | '\t' | '\n' | '\r' | ('\xe2\x80' anything:c ?(0x80 <= ord(c) <= 0x8F))>
docstring = brk:val -> '\\n'.join(val).strip()
cpp_comment = '//' rest_of_line
c_comment = '/*' <(~'*/' anything)*>:body '*/' -> body
python_comment = '#' rest_of_line
rest_of_line = <('\\\n' | (~'\n' anything))*>
immutable = '(' brk 'python.immutable' brk '=' brk '""' brk ')'
'''

RESERVED_TOKENS = (
    '__CLASS__' , '__DIR__' , '__FILE__' , '__FUNCTION__' , '__LINE__' , '__METHOD__' ,
    '__NAMESPACE__' , 'abstract' , #'alias' , # TODO: so many reserved words...
    'and' , 'args' , 'as' , 'assert' , 'BEGIN' ,
    'begin' , 'binary' , 'bool' , 'break' , 'byte' , 'case' , 'catch' , 'class' , 'clone' ,
    'const' , 'continue' , 'declare' , 'def' , 'default' , 'del' , 'delete' , 'do' ,
    'double' , 'dynamic' , 'elif' , 'else' , 'elseif' , 'elsif' , # 'END' , 'end' ,  # TODO: cleaner way to handle use of 'end'
    'enddeclare' , 'endfor' , 'endforeach' , 'endif' , 'endswitch' , 'endwhile' , 'ensure' ,
    'enum' , 'except' , 'exception' , 'exec' , 'extends' , 'finally' , 'float' , 'for' ,
    'foreach' , 'from' , 'function' , 'global' , 'goto' , 'i16' , 'i32' , 'i64' , 'if' ,
    'implements' , 'import' , 'in' , 'include' , 'inline' , 'instanceof' , 'interface' ,
    'is' , 'lambda' , 'list' , 'map' , 'module' , 'namespace' , 'native' , 'new' , 'next' ,
    'nil' , 'not' , 'oneway' , 'optional' , 'or' , 'pass' , 'print' , 'private' ,
    'protected' , 'public' , 'public' , 'raise' , 'redo' , 'register' , 'required' ,
    'rescue' , #'retry' , 
    'return' , 'self' , 'service' , 'set' , 'sizeof' , 'static' ,
    'string' , 'struct' , 'super' , 'switch' , 'synchronized' , 'then' , 'this' ,
    'throw' , 'throws' , 'transient' , 'try' , 'typedef' , 'undef' , 'union' , 'union' ,
    'unless' , 'unsigned' , 'until' , 'use' , 'var' , 'virtual' , 'void' , 'volatile' ,
    'when' , 'while' , 'with' , 'xor' , 'yield')


is_reserved = re.compile('^({0})$'.format('|'.join(RESERVED_TOKENS))).match


BASE_TYPE_MAP = {
    'bool': TType.BOOL,
    'byte': TType.BYTE,
    'i8': TType.BYTE,
    'i16': TType.I16,
    'i32': TType.I32,
    'i64': TType.I64,
    'double': TType.DOUBLE,
    'string': TType.STRING,
    'binary': TType.BINARY
}


PARSER = parsley.makeGrammar(
    GRAMMAR, 
    {
        'Document': collections.namedtuple('Document', 'headers definitions'),
        'Include': _add_include,
        'Definition': _add_definition,
        'Enum': _make_enum,
        '_fill_in_struct': _fill_in_struct,
        'Exception_': _make_exception,
        'Service': _make_service,
        'Function': collections.namedtuple('Function', 'name ttype fields oneway throws docstring'),
        'Field': collections.namedtuple('Field', 'id req ttype name default'),
        'IdentifierRef': _lookup_symbol,
        'BaseTType': BASE_TYPE_MAP.get,
        'TType': TType,
        '_cast_struct': _cast_struct,
        'DeclareStruct': _make_empty_struct,
        '_ref_type': _ref_type,
        '_ref_val': _ref_val,
        '_attr_ttype': _attr_ttype,
        'is_reserved': is_reserved,
    }
)


class ParseError(ThriftGrammerError): pass

