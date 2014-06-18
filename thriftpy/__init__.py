# -*- coding: utf-8 -*-

__version__ = '0.1.3'

import sys
__python__ = sys.version

__all__ = ["install_import_hook", "remove_import_hook", "load"]

from .hook import install_import_hook, remove_import_hook
from .parser import load
