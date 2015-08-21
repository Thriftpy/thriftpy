# -*- coding: utf-8 -*-
import sys


from .hook import install_import_hook, remove_import_hook
from .hook import mount_namespace, umount_namespace
from .parser import load, load_module

__version__ = '0.3.1'
__python__ = sys.version_info
__all__ = [
    "install_import_hook", "remove_import_hook",  "load", "load_module",
    "mount_namespace", "umount_namespace",
]
