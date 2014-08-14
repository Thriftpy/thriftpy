# -*- coding: utf-8 -*-

__version__ = '0.1.6'

import sys
__python__ = sys.version_info

__all__ = ["install_import_hook", "remove_import_hook",  "load", "load_module"]

from .hook import install_import_hook, remove_import_hook
from .parser import load, load_module
