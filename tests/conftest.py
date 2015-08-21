# -*- coding: utf-8 -*-
import os
from functools import partial

import pytest

import thriftpy


@pytest.fixture(scope='function')
def namespace_import(request):

    def namespace(name, path):
        path = os.path.abspath(path)
        thriftpy.mount_namespace(name, path)
        request.addfinalizer(
            partial(thriftpy.umount_namespace, name, path))

    return namespace
