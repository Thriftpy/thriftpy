========
ThriftPy
========

ThriftPy is a pure python implemention of
`Apache Thrift <http://thrift.apache.org/>`_ in a pythonic way.

The official thrift python lib is not pythonic at all, it needs a complicated
process of installation, and the generated sdk is very ugly. Everytime the
thrift file changed you have to re-generate the sdk which causes more pain
in development.

ThriftPy helps that, it's compatible with Apache Thrift so you no longer need
to install 'thrift' package, it can import thrift file on the fly so you
no longer need to re-generate the sdk again and again and again.

Github: https://github.com/eleme/thriftpy


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
    from thriftpy.rpc import make_server

    pingpong = thriftpy.load("pingpong.thrift")

    class Dispatcher(object):
        def ping(self):
            return "pong"

    server = make_server(pingpong.PingPong, Dispatcher(), '127.0.0.1', 6000)
    server.serve()

And a client:

.. code:: python

    import thriftpy
    from thriftpy.rpc import make_client

    pingpong = thriftpy.load("pingpong.thrift")

    client = make_client(pingpong.PingPong, '127.0.0.1', 6000)
    client.ping()

See, it's that easy!

You can refer to 'examples' and 'tests' directory in source code for more
usage examples.



Features
========

Currently ThriftPy have these features (also advantages over the upstream
python lib):

- Supports python2.7 to python3.4 and pypy.

- Compatible with Apache Thirft.  You can use ThriftPy together with the
  official implemention servers and clients, such as a upstream server with
  a thriftpy client or the opposite.

  (Currently only binary protocol & buffered transport were implemented.)

- Can directly load thrift file as module, the sdk code will be generated on
  the fly.

  For example, ``pingpong = thriftpy.load("pingpong.thrift")`` will load
  'pingpong.thrift' as 'pingpong' module.

  Or, when import hook enabled, directly use ``import pingpong_thrift`` to
  import the 'pingpong.thrift' file as module.

- Pure python, standalone implemention. No longer need to compile & install
  the 'thrift' package. All you need is python and thrift file.

- Easy RPC server/client setup.



Installation
============

Install with pip

.. code:: bash

    $ pip install thriftpy

You may also install cython first to build cython extension locally.

.. code:: bash

    $ pip install cython thriftpy


Use Cython Binary Protocol
==========================

.. note::

    The cython binary protocol is still very experimental and the code need to
    be audited. Use with caution.

The TCyBinaryProtocol can be used to accelerate serialize and deserialize.

Pass TCyBinaryProtocolFactory to make_server to enable it.

.. code:: python

    from thriftpy.protocol import TCyBinaryProtocolFactory
    from thriftpy.rpc import make_server

    server = make_server(
        pingpong_thrift.PingPong, Dispatcher(), '127.0.0.1', 6000,
        proto_factory=TCyBinaryProtocolFactory())
    print("serving...")
    server.serve()

The same goes for client.

.. code:: python

    from thriftpy.protocol import TCyBinaryProtocolFactory
    from thriftpy.rpc import make_client

    client = make_client(
        pingpong_thrift.PingPong, '127.0.0.1', 6000,
        proto_factory=TCyBinaryProtocolFactory())
    client.ping()

Or client context:

.. code:: python

    from thriftpy.protocol import TCyBinaryProtocolFactory
    from thriftpy.rpc import client_context

    with client_context(
            pingpong_thrift.PingPong, '127.0.0.1', 6000,
            proto_factory=TCyBinaryProtocolFactory()) as c:
        c.ping()


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


TODOs
=====

Currently ThriftPy is not fully compatible with thrift, I only implemented
the features we need in ele.me.

These todos need to be done, but may not be completed by me in near future,
so contributions are very welcome!

- other protocol and transport except binary and buffered transport.

- map type const.

- 'namespace', 'extends', 'import', 'oneway' etc keywords.

- the '.thrift' file parser will skip a section if it has syntax error. A
  better warning message should be given.


Changelogs
==========

https://github.com/eleme/thriftpy/blob/master/CHANGES


Contribute
==========

1. Fork the repo and make changes.

2. Write a test which shows a bug was fixed or the feature works as expected.

3. Make sure travis-ci test succeed.

4. Send pull request.


Contributors
============

https://github.com/eleme/thriftpy/graphs/contributors
