========
ThriftPy
========

ThriftPy is a pure python implemention of Apache Thrift in a pythonic way.

Documentation: https://thriftpy.readthedocs.org/


Installation
============

Install while pip

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

    from thriftpy.rpc import make_server
    import pingpong_thrift

    class Dispatcher(object):
        def ping(self):
            return "pong"

    server = make_server(pingpong_thrift.PingPong, Dispatcher(), '127.0.0.1', 6000)
    server.serve()

And a client:

.. code:: python

    from thrift.rpc import make_client
    import pingpong_thrift

    client = make_client(pingpong_thrift.PingPong, '127.0.0.1', 6000)
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

- Can import thrift file as normal py modules. The sdk code is generated on
  the fly.

  For example, ``import pingpong_thrift`` will import the 'pingpong.thrift' file
  as module

- Pure python, standalone implemention. No longer need to compile & install
  the 'thrift' package. All you need is python and thrift file.

- Easy RPC server/client setup.


Contribute
==========

1. Fork the repo and make changes.

2. Write a test which shows a bug was fixed or the feature works as expected.

3. Make sure travis-ci test succeed.

4. Send pull request.
