# -*- coding: utf-8 -*-

import thriftpy


def test_import_hook():
    ab_1 = thriftpy.load("addressbook.thrift")
    print("Load file succeed.")
    assert ab_1.DEFAULT_LIST_SIZE == 10

    try:
        import addressbook_thrift as ab  # noqa
    except ImportError:
        print("Import hook not installed.")

    thriftpy.install_import_hook()

    import addressbook_thrift as ab_2
    print("Magic import succeed.")
    assert ab_2.DEFAULT_LIST_SIZE == 10
