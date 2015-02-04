# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import sys
import types

from .parser import load_module, load


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
        return load_module(fullname)


class NamespacePathImporter(object):
    '''
    The namespace importer will hold a package namespace for thrift imports.
    It can be used where you have your idls in a separate directory and want to
    import them like normal python modules without the _thrift extension

    The thrift types imported can be pickled.

    namespace:
        The python package namespace to use for thrift imports.
    path:
        The absolute path to the directory where the namespace is bound
    '''

    suffix = 'thrift'

    def __init__(self, namespace, path):
        '''
        :param str namespace: module namespace e.g. mypkg.thrift.idls
        :param str path: absolute path to the thrift files
        '''
        if os.path.isabs(path) and os.path.isdir(path):
            self.path = path
        else:
            raise TypeError('path must exist and be absolute')
        self.namespace = namespace

    def __eq__(self, other):
        if (isinstance(other, type(self))
                and self.suffix == other.suffix
                and self.namespace == other.namespace):
            return True
        return False

    def find_module(self, fullname, path=None):
        """
        Only supports modules in the defined namespace
        """
        if fullname.startswith(self.namespace):
            return self
        return None

    def load_module(self, fullname):
        """
        :param str fullname: full name of the module e.g foo.bar.baz
        :return: ModuleType
        """
        if fullname in sys.modules:
            return sys.modules[fullname]

        path = self._get_path(fullname)

        # Consider directories as packages
        if os.path.isdir(path):
            return self._create_package(fullname, path)

        idl_fname = '{0}.{1}'.format(path, self.suffix)
        if os.path.isfile(idl_fname):
            thrift_module = load(
                idl_fname,
                module_name=fullname,
                include_dir=self._get_path(),
            )
            thrift_module.__name__ = fullname
            thrift_module.__loader__ = self
            thrift_module.__file__ = idl_fname
            thrift_module.__package__ = '.'.join(fullname.split('.')[:-1])
            sys.modules[fullname] = thrift_module
            return thrift_module

        raise ImportError('Unable to resolve {0}'.format(fullname))

    def _create_package(self, name, path):
        """
        :param str name: full name of package to be created
        :param str path: absolute path to the directory
        """
        package = types.ModuleType(name)
        package.__name__ = name
        package.__path__ = [path]
        package.__loader__ = self
        package.__file__ = path
        _parent, _child = os.path.splitext(name)
        if not _child:
            _parent = ''
        package.__package__ = _parent
        sys.modules[name] = package

        return package

    def _get_path(self, name=''):
        """
        :param str name: name of the idl module.
        :return: absolute path to the module file/directory
        """
        name = name[len(self.namespace)+1:].replace('.', os.path.sep)
        return os.path.join(self.path, name)

_imp = ThriftImporter()


def mount_namespace(namespace, path, list_modules=False):
    importer = NamespacePathImporter(namespace, path)
    sys.meta_path[:] = [x for x in sys.meta_path if x != importer] + [importer]


def umount_namespace(namespace, path, list_modules=False):
    importer = NamespacePathImporter(namespace, path)
    sys.meta_path[:] = [x for x in sys.meta_path if importer != x]


def install_import_hook():
    global _imp
    sys.meta_path[:] = [x for x in sys.meta_path if _imp != x] + [_imp]


def remove_import_hook():
    global _imp
    sys.meta_path[:] = [x for x in sys.meta_path if _imp != x]
