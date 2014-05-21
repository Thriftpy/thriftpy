# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from setuptools.extension import Extension

version = "0.1.0"

install_requires = [
    "pyparsing>=2.0.1",
]

dev_requires = [
    "cython>=0.20.1",
    "flake8>=2.1.0",
]


try:
    from Cython.Distutils import build_ext
    cython = True
except ImportError:
    cython = False

cmdclass = {}
ext_modules = []

if cython:
    ext_modules.append(Extension("thriftpy.protocol.cybinary",
                                 ["thriftpy/protocol/cybinary.pyx"]))
    cmdclass["build_ext"] = build_ext
else:
    ext_modules.append(Extension("thriftpy.protocol.cybinary",
                                 ["thriftpy/protocol/cybinary.c"]))


setup(name="thriftpy",
      version=version,
      description="Pure python implemention of Apache Thrift.",
      keywords="thrift python thriftpy",
      author="Lx Yu",
      author_email="i@lxyu.net",
      packages=find_packages(exclude=['benchmark', 'docs', 'tests']),
      entry_points={},
      url="http://lxyu.github.io/thriftpy/",
      license="MIT",
      zip_safe=False,
      long_description=open("README.rst").read(),
      install_requires=install_requires,
      extras_require={
          "dev": dev_requires,
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
      ])
