# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from Cython.Build import cythonize

version = "0.1.0"

install_requires = [
    "cython>=0.20.1",
    "pyparsing>=2.0.1",
]

dev_requires = [
    "flake8>=2.1.0",
]

setup(name="thriftpy",
      version=version,
      description="Pure python implemention of Apache Thrift.",
      keywords="thrift python thriftpy",
      author="Lx Yu",
      author_email="i@lxyu.net",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      entry_points={},
      url="http://lxyu.github.io/thriftpy/",
      license="MIT",
      zip_safe=False,
      long_description=open("README.rst").read(),
      install_requires=install_requires,
      extras_require={
          "dev": dev_requires,
      },
      ext_modules=cythonize(["thriftpy/protocol/cybinary.pyx"]),
      classifiers=[
          "Topic :: Software Development"
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
      ])
