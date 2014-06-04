# -*- coding: utf-8 -*-

import os
import sys

from .parser import load


class ThriftImporter(object):
    def __init__(self, extension="_thrift"):
        self.extension = extension

    def __eq__(self, other):
        return self.__class__.__module__ == other.__class__.__module__ and \
            self.__class__.__name__ == other.__class__.__name__ and \
            self.extension == other.extension

    def find_module(self, fullname, path=None):
        if fullname.endswith(self.extension):
            return self

    def load_module(self, fullname):
        if '.' in fullname:
            module_name, thrift_file = fullname.rsplit('.', 1)
            module = self._import_module(module_name)
            path_prefix = os.path.dirname(os.path.abspath(module.__file__))
            path = os.path.join(path_prefix, thrift_file)
        else:
            path = fullname
        filename = path.replace('_', '.', 1)
        thrift = load(filename)
        sys.modules[fullname] = thrift
        return thrift

    def _import_module(self, import_name):
        if '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
            return getattr(__import__(module, None, None, [obj]), obj)
        else:
            return __import__(import_name)
_imp = ThriftImporter()


def install_import_hook():
    global _importer
    sys.meta_path[:] = [x for x in sys.meta_path if _imp != x] + [_imp]


def remove_import_hook():
    global _importer
    sys.meta_path[:] = [x for x in sys.meta_path if _imp != x]
