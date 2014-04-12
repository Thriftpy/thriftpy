ThriftPY
========

(Still under developing...)

Pure python implemention of Apache Thrift in a pythonic way.

It currently supports python2.7 or higher & python3.3 or higher.


Features
--------

* Compatiable with Apache Thirft. (Currently only compatiable with binary
  protocol & buffered transport.)

* Pure python implemention, no longer need to compile & install the `thrift`
  package.

* Dynamic generate sdk codes. No need for code generator.

* `.thrift` file can be directly import with `_thrift`, such as `import
  addressbook_thrift`

* Easy rpc server/client setup.


Install
-------

Install while pip

.. code:: bash

    $ pip install thriftpy


Usage
-----

Refer to `tests/` for example.
