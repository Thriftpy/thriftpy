# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys

from .parser import load_module


class ThriftImporter(object):
    def __init__(self, extension="_thrift"):
        self.extension = extension

    def __eq__(self, other):
        if not other or not isinstance(other, self.__class__):
            return False
        return self.extension == other.extension

    def find_module(self, fullname, path=None):
        if fullname.endswith(self.extension):
            return self

    @classmethod
    def load_module(cls, fullname):
        return load_module(fullname)


_imp = ThriftImporter()


def install_import_hook():
    global _imp
    sys.meta_path[:] = [x for x in sys.meta_path if _imp != x] + [_imp]


def remove_import_hook():
    global _imp
    sys.meta_path[:] = [x for x in sys.meta_path if _imp != x]
