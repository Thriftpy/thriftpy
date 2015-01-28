# -*- coding: utf-8 -*-

"""
    thriftpy.trace
    ~~~~~~~~~~~~~~

    utilities for tracing
"""

from __future__ import absolute_import

import os
from ..parser import load


method_name = "__thriftpy_tracing_method_name__"
thrift = load(os.path.join(os.path.dirname(__file__), "tracing.thrift"))
