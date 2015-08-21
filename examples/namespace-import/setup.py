#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='thrift-tutorial',
    version='1.0.0',
    author='Me',
    author_email='me@example.com',
    packages=find_packages(),
    package_data={
        'example': ['idl/*'],
    },
    entry_points={
        'console_scripts': [
            'calculator-server = example.__main__:main'
        ],
    },
    install_requires=[
        'cython',
        'thriftpy',
    ],
)
