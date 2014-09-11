========
ThriftPy
========

.. image:: http://img.shields.io/travis/eleme/thriftpy/master.svg?style=flat
   :target: https://travis-ci.org/eleme/thriftpy

.. image:: http://img.shields.io/github/release/eleme/thriftpy.svg?style=flat
   :target: https://github.com/eleme/thriftpy/releases

.. image:: http://img.shields.io/pypi/v/thriftpy.svg?style=flat
   :target: https://pypi.python.org/pypi/thriftpy

.. image:: http://img.shields.io/pypi/dm/thriftpy.svg?style=flat
   :target: https://pypi.python.org/pypi/thriftpy

ThriftPy is a pure python implemention of
`Apache Thrift <http://thrift.apache.org/>`_ in a pythonic way.

Documentation: https://thriftpy.readthedocs.org/


Installation
============

Install with pip

.. code:: bash

    $ pip install thriftpy

You may also install cython first to build cython extension locally.

.. code:: bash

    $ pip install cython thriftpy


Code Demo
=========

ThriftPy make it super easy to write server/client code with thrift. Let's
checkout this simple pingpong service demo.

We need a 'pingpong.thrift' file:

::

    service PingPong {
        string ping(),
    }

Then we can make a server:

.. code:: python

    import thriftpy
    pingpong_thrift = thriftpy.load("pingpong.thrift", module_name="pingpong_thrift")

    from thriftpy.rpc import make_server

    class Dispatcher(object):
        def ping(self):
            return "pong"

    server = make_server(pingpong_thrift.PingPong, Dispatcher(), '127.0.0.1', 6000)
    server.serve()

And a client:

.. code:: python

    import thriftpy
    pingpong_thrift = thriftpy.load("pingpong.thrift", module_name="pingpong_thrift")

    from thriftpy.rpc import make_client

    client = make_client(pingpong_thrift.PingPong, '127.0.0.1', 6000)
    client.ping()

See, it's that easy!

You can refer to 'examples' and 'tests' directory in source code for more
usage examples.



Features
========

Currently ThriftPy have these features (also advantages over the upstream
python lib):

- Supports python2.7+, python3.3+, pypy and pypy3.

- Compatible with Apache Thirft.  You can use ThriftPy together with the
  official implemention servers and clients, such as a upstream server with
  a thriftpy client or the opposite.

  Currently implemented protocols and transports:

  * binary protocol (python and cython)

  * buffered transport (python & cython)

  * tornado server and client (with tornado 4.0)

  * framed transport

  * json protocol

- Can directly load thrift file as module, the sdk code will be generated on
  the fly.

  For example, ``pingpong_thrift = thriftpy.load("pingpong.thrift", module_name="pingpong_thrift")``
  will load 'pingpong.thrift' as 'pingpong_thrift' module.

  Or, when import hook enabled by ``thriftpy.install_import_hook()``, you can
  directly use ``import pingpong_thrift`` to import the 'pingpong.thrift' file
  as module, you may also use ``from pingpong_thrift import PingService`` to
  import specific object from the thrift module.

- Pure python implemention. No longer need to compile & install the 'thrift'
  package. All you need is thriftpy and thrift file.

- Easy RPC server/client setup.


Benchmarks
==========

Some benchmark results::

    # apache thrift py binary
    binary protocol struct benchmark for 100000 times:
    encode  -> 3.74061203003
    decode  -> 5.02829790115

    # apache thrift c binary
    accelerated protocol struct benchmark for 100000 times:
    encode  -> 0.398949146271
    decode  -> 0.536000013351

    # thriftpy & pypy2.3
    binary protocol struct benchmark for 100000 times:
    encode  -> 0.413738965988
    decode  -> 0.605606079102

    # thriftpy & py3.4
    binary protocol struct benchmark for 100000 times:
    encode  -> 3.291545867919922
    decode  -> 4.337666034698486

    # thriftpy & py3.4 + cython
    cybin protocol struct benchmark for 100000 times:
    encode  -> 0.5828649997711182
    decode  -> 0.8259570598602295

Checkout the `benchmark/benchmark.rst` for detailed benchmark scripts and
scores.


Changelogs
==========

https://github.com/eleme/thriftpy/blob/master/CHANGES.rst


Contribute
==========

1. Fork the repo and make changes.

2. Write a test which shows a bug was fixed or the feature works as expected.

3. Make sure travis-ci test succeed.

4. Send pull request.


Contributors
============

https://github.com/eleme/thriftpy/graphs/contributors
