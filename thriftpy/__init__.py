"""thriftpy is now a thin alias for thriftpy2.

Every ``thriftpy[.*]`` import resolves to the same object as its ``thriftpy2``
twin, so legacy ``import thriftpy`` code runs on the maintained thriftpy2.
"""

import importlib
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_loader

import thriftpy2

_SRC = "thriftpy2"
_DST = "thriftpy"


class _AliasLoader(Loader):
    def __init__(self, real_name):
        self.real_name = real_name

    def create_module(self, spec):
        return importlib.import_module(self.real_name)

    def exec_module(self, module):
        pass


class _AliasFinder(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname != _DST and not fullname.startswith(_DST + "."):
            return None
        return spec_from_loader(fullname, _AliasLoader(_SRC + fullname[len(_DST):]))


# Intercept thriftpy.* before the default finders look on disk.
if not any(isinstance(f, _AliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _AliasFinder())

from thriftpy2 import (  # noqa: E402
    install_import_hook,
    load,
    load_fp,
    load_module,
    remove_import_hook,
)

__version__ = thriftpy2.__version__
__python__ = sys.version_info
__all__ = ["install_import_hook", "remove_import_hook", "load", "load_module",
           "load_fp"]
