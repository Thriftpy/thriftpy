# -*- coding: utf-8 -*-

__version__ = '0.1.15'

import sys
__python__ = sys.version_info

__all__ = [
    "install_import_hook", "remove_import_hook",
    "mount_namespace", "umount_namespace",
    "load", "load_module",
]

from .hook import install_import_hook, remove_import_hook
from .hook import mount_namespace, umount_namespace
from .parser import load, load_module
