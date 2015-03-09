#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys

from os.path import join, dirname

from setuptools import setup, find_packages
from setuptools.extension import Extension

with open(join(dirname(__file__), 'thriftpy', '__init__.py'), 'r') as f:
    version = re.match(r".*__version__ = '(.*?)'", f.read(), re.S).group(1)

install_requires = [
    "ply==3.4",
]

tornado_requires = [
    "tornado>=4.0,<5.0",
    "toro==0.6"
]

dev_requires = [
    "cython>=0.20.2",
    "flake8>=2.3.0",
    "pytest>=2.6.0",
    "sphinx-rtd-theme>=0.1.6",
    "sphinx>=1.2.2",
] + tornado_requires


# cython detection
try:
    from Cython.Build import cythonize
    CYTHON = True
except ImportError:
    CYTHON = False

cmdclass = {}
ext_modules = []

# pypy detection
PYPY = "__pypy__" in sys.modules

# only build ext in CPython
if not PYPY:
    if CYTHON:
        cythonize("thriftpy/transport/cybase.pyx")
        cythonize("thriftpy/transport/**/*.pyx")
        cythonize("thriftpy/protocol/cybin/cybin.pyx")

    ext_modules.append(Extension("thriftpy.transport.cybase",
                                 ["thriftpy/transport/cybase.c"]))
    ext_modules.append(Extension("thriftpy.transport.buffered.cybuffered",
                                 ["thriftpy/transport/buffered/cybuffered.c"]))
    ext_modules.append(Extension("thriftpy.transport.memory.cymemory",
                                 ["thriftpy/transport/memory/cymemory.c"]))
    ext_modules.append(Extension("thriftpy.transport.framed.cyframed",
                                 ["thriftpy/transport/framed/cyframed.c"]))
    ext_modules.append(Extension("thriftpy.protocol.cybin",
                                 ["thriftpy/protocol/cybin/cybin.c"]))

setup(name="thriftpy",
      version=version,
      description="Pure python implementation of Apache Thrift.",
      keywords="thrift python thriftpy",
      author="Lx Yu",
      author_email="i@lxyu.net",
      packages=find_packages(exclude=['benchmark', 'docs', 'tests']),
      package_data={"thriftpy": ["contrib/tracking/tracking.thrift"]},
      entry_points={},
      url="https://thriftpy.readthedocs.org/",
      license="MIT",
      zip_safe=False,
      long_description=open("README.rst").read(),
      install_requires=install_requires,
      tests_require=tornado_requires,
      extras_require={
          "dev": dev_requires,
          "tornado": tornado_requires
      },
      cmdclass=cmdclass,
      ext_modules=ext_modules,
      classifiers=[
          "Topic :: Software Development",
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: Implementation :: PyPy",
      ])
