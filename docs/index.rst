========
ThriftPy
========

ThriftPy is a pure python implemention of Apache Thrift in a pythonic way.

The official thrift python lib is not pythonic at all, it needs a complicated
process of installation, and the generated sdk is very ugly. Everytime the
thrift file changed you have to re-generate the sdk which causes more pain
in development.

ThriftPy helps that, it's compatiable with Apache Thrift so you no longer need
to install 'thrift' package, it can import thrift file on the fly so you
no longer need to re-generate the sdk again and again and again.

Github: https://github.com/Eleme/thriftpy


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
    from thrift.rpc import make_client

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

- Compatiable with Apache Thirft.  You can use ThriftPy together with the
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

Install while pip

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


TODOS
=====

Currently ThriftPy is not fully compatiable with thrift, I only implemented
the features we need in *ele.me*.

These todos need to be done, but may not be completed by me in near future,
so contributions are very welcome!

- other protocol and transport except binary and buffered transport.

- Cython binary protocol code audit & C Binary extension.

  I'm not good at C or Cython programming so the cython implemention may have
  issues and need to be audited. The cython binary protocol implemention is
  about 2-3 times faster than the python binary protocol, but still many times
  slower than the official C extension. A better c extension needed.

- map type const.

- 'namespace', 'extends', 'import', 'oneway' keywords.

- the '.thrift' file parser will skip a section if it has syntax error. A
  better warning message should be given.


Contribute
==========

1. Fork the repo and make changes.

2. Write a test which shows a bug was fixed or the feature works as expected.

3. Make sure travis-ci test succeed.

4. Send pull request.
