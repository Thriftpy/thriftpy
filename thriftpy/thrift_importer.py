#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import imp
import ihooks
from .parser import load_thrift

THRIFT_SUFFIX = ".thrift"
THRIFT_FILE = 228

def insert_module(module_name, filename, file=None):
    ''' TODO: rename this func '''
    mod = load_thrift(module_name, filename, file)
    sys.modules[name] = mod
    return mod

class ThriftHooks(ihooks.Hooks):
    def get_suffixes(self):
        # add our suffixes
        L = imp.get_suffixes()
        return L + [(THRIFT_SUFFIX , 'r', THRIFT_FILE)]

class ThriftImporter(ihooks.ModuleLoader):

    def load_module(self, name, stuff):
        file, filename, info = stuff
        (suff, mode, type) = info

        if type == THRIFT_FILE:
            return insert_module(name, filename, file)
        else:
            return ihooks.ModuleLoader.load_module( self, name, stuff)

_installed = 0

def install():
    global _installed
    if not _installed:
        hooks = ThriftHooks()
        loader = ThriftImporter(hooks)
        importer = ihooks.ModuleImporter(loader)
        ihooks.install(importer)
        _installed = 1
