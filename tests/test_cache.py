#!/usr/bin/env python2
# -*- coding: utf8 -*-

from __future__ import absolute_import, division, print_function
import time

__metaclass__ = type
__author__ = 'y'
__date__ = '14-6-17'
# __all__ = []

"""
"""
import thriftpy

# set this var
thrift_file = ''


def gen_cache():
    print('gen_cache')
    st = time.time()
    thriftpy.load(thrift_file)
    cost = time.time() - st
    print(cost)


def use_cache():
    print('use_cache')
    st = time.time()
    thriftpy.load(thrift_file)
    cost = time.time() - st
    print(cost)


def no_cache():
    print('no_cache')
    st = time.time()
    thriftpy.load(thrift_file, cache=False)
    cost = time.time() - st
    print(cost)


gen_cache()
use_cache()
no_cache()
