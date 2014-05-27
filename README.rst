ThriftPy
========

ThriftPy is a pure python implemention of Apache Thrift in a pythonic way.

The official thrift python lib is not pythonic at all, it needs a complicate
process of installation, and the generated sdk is very ugly. Everytime the
thrift file changed you have to re-generate the sdk which causes more pain
in development.

ThriftPy helps that, it's compatiable with Apache Thrift so you no longer need
to install 'thrift' package, and it can import thrift file on the fly so you
no longer need to re-generate the sdk again and again and again.


Usage Sample
------------

ThriftPy make it easy to write server/client code upon thrift, see this
simple ping-pong service example.

`pingpong.thrift` file:

::

    service PingPong {
        string ping(),
    }

Server-side code:

.. code:: python

    from thriftpy.rpc import make_server
    import pingpong_thrift as pingpong

    class Dispatcher(object):
        def ping(self):
            return "pong"

    server = make_server(pingpong.PingPong, Dispatcher(), '127.0.0.1', 6000)
    server.serve()

Client-side code:

.. code:: python

    from thrift.rpc import make_client
    import pingpong_thrift as pingpong

    client = make_client(pingpong.PingPong, '127.0.0.1', 6000)
    client.ping()

See, it's that easy!

You can refer to `examples` and `tests` for more usage demo.

ThirftPy is compatiable with Apache Thrift so you can use it together with
the official implemention of server/client.


Features
--------

* Supports python2.7(or higher) & python3.3(or higher).

* Compatiable with Apache Thirft. (Currently only compatiable with binary
  protocol & buffered transport.)

* Pure python implemention, no longer need to compile & install the `thrift`
  package.

* Dynamic generate sdk codes. No need for code generator.

* `.thrift` file can be directly import with `_thrift`, such as `import
  addressbook_thrift`

* Easy RPC server/client setup.


Install
-------

Install while pip

.. code:: bash

    $ pip install thriftpy

You may also install cython first and it'll build cython extension locally.

.. code:: bash

    $ pip install cython thriftpy


TODOS
-----

Currently ThriftPy is not fully compatiable with thrift, I only implemented
the features we need in Eleme.

These features are *NOT* implemented yet, and may not be implemented in near
future, so contributions are very welcome!

* Cython binary protocol code audit & C Binary extension.

  I'm not good at C or Cython programming so the cython implemention may have
  issues and need to be audited. The cython binary protocol implemention is
  about 2-3 times faster than the python binary protocol, but still many times
  slower than the official C extension. A better c extension needed.

* map type const.

* `namespace`, `extends`, `import`, `oneway` keywords


Contribute
----------

1. Fork the repo and make changes.

2. Write a test which shows a bug was fixed or the feature works as expected.

3. Make sure travis-ci test succeed.

4. Send pull request.
