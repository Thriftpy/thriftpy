#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from setuptools.extension import Extension

install_requires = [
    "pyparsing>=2.0.2,<2.1.0",
]

tornado_requires = [
    "tornado>=4.0,<5.0",
    "toro"
]

dev_requires = [
    "cython>=0.20.2",
    "flake8>=2.2.2",
    "pytest>=2.6.0",
    "sphinx-rtd-theme>=0.1.6",
    "sphinx>=1.2.2",
] + tornado_requires


try:
    from Cython.Distutils import build_ext
    cython = True
except ImportError:
    cython = False

cmdclass = {}
ext_modules = []

if cython:
    ext_modules.append(Extension("thriftpy.protocol.cybin",
                                 ["thriftpy/protocol/cybin/cybin.pyx"]))
    cmdclass["build_ext"] = build_ext
else:
    ext_modules.append(Extension("thriftpy.protocol.cybin",
                                 ["thriftpy/protocol/cybin/cybin.c"]))

setup(name="thriftpy",
      version=__import__('thriftpy').__version__,
      description="Pure python implemention of Apache Thrift.",
      keywords="thrift python thriftpy",
      author="Lx Yu",
      author_email="i@lxyu.net",
      packages=find_packages(exclude=['benchmark', 'docs', 'tests']),
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
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: Implementation :: PyPy",
      ])
