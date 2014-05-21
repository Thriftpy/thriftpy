# -*- coding: utf-8 -*-
# flake8: noqa

"""
    thriftpy._compat
    ~~~~~~~~~~~~~

    py2/py3 compatibility support.
"""


import sys

PY3 = sys.version_info[0] == 3


if PY3:
    text_type = str
    string_types = (str,)

    def u(s):
        return s
else:
    text_type = unicode
    string_types = (str, unicode)

    def u(s):
        if not isinstance(s, text_type):
            s = s.decode("utf-8")
        return s
