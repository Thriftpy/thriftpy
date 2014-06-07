# -*- coding: utf-8 -*-

"""
    thriftpy._compat
    ~~~~~~~~~~~~~

    py2/py3 compatibility support.
"""

import sys
PY3 = sys.version_info[0] == 3

import types


if PY3:
    text_type = str
    string_types = (str,)

    def u(s):
        return s
else:
    text_type = unicode  # noqa
    string_types = (str, unicode)  # noqa

    def u(s):
        if not isinstance(s, text_type):
            s = s.decode("utf-8")
        return s


def init_func_generator(spec):
    """Generate `__init__` function based on TPayload.default_spec

    For example::

        spec = [('name', 'Alice'), ('number', None)]

    will generate::

        def __init__(self, name='Alice', number=None):
            kwargs = locals()
            kwargs.pop('self')
            self.__dict__.update(kwargs)

    TODO: The `locals()` part may need refine.
    """
    varnames, defaults = zip(*spec)
    varnames = ('self', ) + varnames

    def init(self):
        kwargs = locals()
        kwargs.pop('self')
        self.__dict__.update(kwargs)

    code = init.__code__
    if PY3:
        new_code = types.CodeType(len(spec) + 1,
                                  0,
                                  len(spec) + 2,
                                  code.co_stacksize,
                                  code.co_flags,
                                  code.co_code,
                                  code.co_consts,
                                  code.co_names,
                                  varnames,
                                  code.co_filename,
                                  "__init__",
                                  code.co_firstlineno,
                                  code.co_lnotab,
                                  code.co_freevars,
                                  code.co_cellvars)
    else:
        new_code = types.CodeType(len(spec) + 1,
                                  len(spec) + 2,
                                  code.co_stacksize,
                                  code.co_flags,
                                  code.co_code,
                                  code.co_consts,
                                  code.co_names,
                                  varnames,
                                  code.co_filename,
                                  "__init__",
                                  code.co_firstlineno,
                                  code.co_lnotab,
                                  code.co_freevars,
                                  code.co_cellvars)

    return types.FunctionType(new_code,
                              {"__builtins__": __builtins__},
                              argdefs=defaults)
