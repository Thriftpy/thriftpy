# -*- coding: utf-8 -*-

"""
    thriftpy.parser
    ~~~~~~~~~~~~~~~

    Thrift parser using ply
"""

from __future__ import absolute_import

import itertools
import os
import os.path
import sys
import types

from .model import IdentifierValue
from .parser import parse
from ..thrift import gen_init, TException, TPayload, TType


_thriftloader = {}


def load(thrift_file, module_name=None, include_dirs=None):
    """Load thrift_file as a module

    The module loaded and objects inside may only be pickled if module_name
    was provided.
    """
    if module_name and not module_name.endswith("_thrift"):
        raise ValueError(
            "ThriftPy can only generate module with '_thrift' suffix")

    include_dirs = list(include_dirs or ["."])

    global _thriftloader
    # if module_name provided, it should be unique. we'll ignore the filename
    # here for the global thriftloader
    _thriftloader_key = module_name or thrift_file
    if _thriftloader_key in _thriftloader:
        return _thriftloader[_thriftloader_key]

    real_module = bool(module_name)

    # generate a fake module_name when it's not provided
    if not module_name:
        basename = os.path.basename(thrift_file)
        module_name, _ = os.path.splitext(basename)

    exception = None
    for d in include_dirs:
        try:
            path = os.path.join(d, thrift_file)
            with open(path, "r") as fp:
                schema = fp.read()
        except IOError as e:
            exception = e
        else:
            exception = None
            break

    if exception is not None:
        raise exception

    result = parse(schema)

    # load thrift schema as module
    thrift_schema = types.ModuleType(module_name)
    _type = lambda n, o: type(n, (o, ), {"__module__": module_name})

    def make_thrift_include_name(path):
        name = os.path.basename(path)
        assert name.endswith(".thrift")
        return name[:-len(".thrift")]

    thrift_schema._includes = {}
    for path in result["includes"]:
        name = make_thrift_include_name(path)
        include = thrift_schema._includes[name] = load(
            path, include_dirs=include_dirs)
        setattr(thrift_schema, name, include)

    thrift_schema._struct_names = list(itertools.chain(
        result["structs"].keys(),
        result["unions"].keys(),
        result["exceptions"].keys()))

    thrift_schema._enums = result["enums"]
    thrift_schema._typedefs = result["typedefs"]

    def _ttype(t, module=None):
        module = module or thrift_schema
        if isinstance(t, str):
            if "." in t:
                include, field = t.split(".", 1)
                return _ttype(field, module=module._includes[include])
            elif t in module._struct_names:
                return TType.STRUCT, getattr(module, t)
            elif t in module._enums:
                return TType.I32, getattr(module, t)
            elif t in module._typedefs:
                return _ttype(module._typedefs[t])
            else:
                return getattr(TType, t.upper())
        elif t[0] == "list":
            return TType.LIST, _ttype(t[1])
        elif t[0] == "set":
            return TType.SET, _ttype(t[1])
        elif t[0] == "map":
            return TType.MAP, (_ttype(t[1]), _ttype(t[2]))
        else:
            raise Exception("ttype parse error: {0}".format(t))

    def _lookup_value(const):
        if isinstance(const, IdentifierValue):
            value = thrift_schema
            for ref in const.v.split("."):
                value = getattr(value, ref)
            return value

        return const

    def _ttype_spec(ttype, name):
        ttype = _ttype(ttype)
        if isinstance(ttype, int):
            return ttype, name
        else:
            return ttype[0], name, ttype[1]

    # load enums
    for name, enum in result["enums"].items():
        attrs = {"__module__": module_name}
        v2n, n2v = {}, {}
        for key, value in enum.items():
            attrs[key] = value
            v2n[value] = key
            n2v[key] = value
        attrs['_VALUES_TO_NAMES'] = v2n
        attrs['_NAMES_TO_VALUES'] = n2v
        enum_cls = type(name, (object, ), attrs)
        setattr(thrift_schema, name, enum_cls)

    # load consts
    for name, value in result["consts"].items():
        setattr(thrift_schema, name, _lookup_value(value))

    # load structs/unions
    for name in itertools.chain(result["structs"].keys(),
                                result["unions"].keys()):
        attrs = {"__module__": module_name}
        struct_cls = type(name, (TPayload, ), attrs)
        setattr(thrift_schema, name, struct_cls)

    for name in result["exceptions"].keys():
        attrs = {"__module__": module_name}
        exc_cls = type(name, (TException, ), attrs)
        setattr(thrift_schema, name, exc_cls)

    for name, struct in itertools.chain(result["structs"].items(),
                                        result["unions"].items(),
                                        result["exceptions"].items()):
        thrift_spec, default_spec = {}, []
        for m in struct:
            thrift_spec[m["id"]] = _ttype_spec(m["type"], m["name"])
            default = _lookup_value(m["value"]) if m["value"] else None
            default_spec.append((m["name"], default))
        struct_cls = getattr(thrift_schema, name)
        gen_init(struct_cls, thrift_spec, default_spec)

    # load services
    for name, service in result["services"].items():
        base = _BaseService
        if service["extends"]:
            module, extends_name = thrift_schema, service["extends"]
            if "." in service["extends"]:
                module_name, extends_name = service["extends"].split(".", 1)
                module = module._includes[module_name]

            base = getattr(module, extends_name)

        assert hasattr(base, "thrift_services"), \
            "%s is not a valid service base" % (service["extends"])

        service_cls = _type(name, base)
        thrift_services = []
        for api_name, api in service["apis"].items():
            thrift_services.append(api_name)

            # generate default spec from thrift spec
            _default_spec = lambda s: [(s[k][1], None) for k in sorted(s)]

            # api args payload
            args_name = "%s_args" % api_name
            args_attrs = {"__module__": module_name}

            args_thrift_spec = {}
            for field in api["fields"]:
                args_thrift_spec[field["id"]] = _ttype_spec(field["type"],
                                                            field["name"])
            args_cls = type(args_name, (TPayload, ), args_attrs)
            gen_init(args_cls, args_thrift_spec,
                     _default_spec(args_thrift_spec))
            setattr(service_cls, args_name, args_cls)

            # api result payload
            result_name = "%s_result" % api_name
            result_attrs = {"__module__": module_name}

            # if oneway
            result_attrs["oneway"] = api["oneway"]

            if api["type"] == "void":
                result_thrift_spec = {}
            else:
                result_thrift_spec = {0: _ttype_spec(api["type"], "success")}

            if api.get("throws"):
                for t in api["throws"]:
                    result_thrift_spec[t["id"]] = _ttype_spec(t["type"],
                                                              t["name"])

            result_cls = type(result_name, (TPayload, ), result_attrs)
            gen_init(result_cls, result_thrift_spec,
                     _default_spec(result_thrift_spec))
            setattr(service_cls, result_name, result_cls)

        service_cls.thrift_services = base.thrift_services + thrift_services
        setattr(thrift_schema, name, service_cls)
    thrift_schema.__file__ = thrift_file

    _thriftloader[_thriftloader_key] = thrift_schema
    # insert into sys.modules if module_name was provided manually
    if real_module:
        sys.modules[module_name] = _thriftloader[_thriftloader_key]
    return _thriftloader[_thriftloader_key]


def _import_module(import_name):
    if '.' in import_name:
        module, obj = import_name.rsplit('.', 1)
        return getattr(__import__(module, None, None, [obj]), obj)
    else:
        return __import__(import_name)


def load_module(fullname):
    """Load thrift_file by fullname, fullname should have '_thrift' as
    suffix.

    The loader will replace the '_thrift' with '.thrift' and use it as
    filename to locate the real thrift file.
    """
    if not fullname.endswith("_thrift"):
        raise ImportError(
            "ThriftPy can only load module with '_thrift' suffix")

    if fullname in sys.modules:
        return sys.modules[fullname]

    if '.' in fullname:
        module_name, thrift_module_name = fullname.rsplit('.', 1)
        module = _import_module(module_name)
        path_prefix = os.path.dirname(os.path.abspath(module.__file__))
        path = os.path.join(path_prefix, thrift_module_name)
    else:
        path = fullname
    thrift_file = "{0}.thrift".format(path[:-7])

    module = load(thrift_file, module_name=fullname)
    sys.modules[fullname] = module
    return sys.modules[fullname]


class _BaseService(object):
    thrift_services = []
