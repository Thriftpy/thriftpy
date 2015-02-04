# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import sys
import pickle

import pytest

import thriftpy
from thriftpy.hook import NamespacePathImporter

pickled_data = b"ccopy_reg\n_reconstructor\np0\n(cthriftpy.dummynamespace.structs\nPerson\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nS'address'\np6\nS'123 Milky Way Street'\np7\nsS'name'\np8\nS'Jane Doe'\np9\nsb."  # noqa


def test_namespace_import(namespace_import):
    with pytest.raises(ImportError):
        import dummynamespace  # noqa

    ct_1 = thriftpy.load('parser-cases/constants.thrift')

    assert ct_1.Country.US == 1

    namespace_import('dummynamespace', 'parser-cases')

    from dummynamespace import constants

    assert sys.modules['dummynamespace.constants'] == constants
    assert constants.Country.US == 1


def test_namespace_import_pickle(namespace_import):

    namespace_import('thriftpy.dummynamespace', 'parser-cases')

    from thriftpy.dummynamespace.structs import Person

    person = Person('Jane Doe', '123 Milky Way Street')
    person_2 = pickle.loads(pickled_data)
    assert person == person_2


def test_namespace_import_meta(namespace_import):

    namespace_import('mypkg', 'parser-cases')

    import mypkg

    assert os.path.basename(mypkg.__file__.rstrip('/')) == 'parser-cases'
    assert mypkg.__name__ == 'mypkg'
    assert mypkg.__package__ == ''
    assert os.path.basename(mypkg.__path__[0].rstrip('/')) == 'parser-cases'

    loader = mypkg.__loader__

    assert os.path.basename(loader.path) == 'parser-cases'
    assert loader.namespace == 'mypkg'
    assert isinstance(loader, NamespacePathImporter)

    import mypkg.constants as ct

    assert os.path.basename(ct.__file__) == 'constants.thrift'
    assert ct.__name__ == 'mypkg.constants'
    assert ct.__package__ == 'mypkg'
    with pytest.raises(AttributeError):
        ct.__path__
