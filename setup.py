# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from setuptools.extension import Extension
import sys
import os

version = "0.1.3"

install_requires = [
    "pyparsing==2.0.2",
]

dev_requires = [
    "cython>=0.20.1",
    "flake8>=2.1.0",
    "nose>=1.3.3",
    "sphinx-rtd-theme>=0.1.6",
    "sphinx>=1.2.2",
]


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

    class ExtBuilder(build_ext, object):
        def run(self):
            self.generate_config()
            super(ExtBuilder, self).run()

        def generate_config(self):
            if sys.version_info.major == 3:
                config = 'DEF PY3=1\nDEF PY2=0\n'
            else:
                config = 'DEF PY3=0\nDEF PY2=1\n'
            path = os.path.join(
                os.path.dirname(__file__),
                'thriftpy', 'protocol', 'cybin', 'cybin_config.pxi'
            )
            with open(path, 'w') as f:
                f.write(config)
    cmdclass["build_ext"] = ExtBuilder
else:
    ext_modules.append(Extension("thriftpy.protocol.cybin",
                                 ["thriftpy/protocol/cybin/cybin.c"]))


setup(name="thriftpy",
      version=version,
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
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: Implementation :: PyPy",
      ])
