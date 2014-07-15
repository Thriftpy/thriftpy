#!/usr/bin/env python2
# -*- coding: utf8 -*-

import time
import thriftpy

# set this var
thrift_file = 'addressbook.thrift'


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
