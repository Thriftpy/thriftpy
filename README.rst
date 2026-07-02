========
ThriftPy
========

``thriftpy`` is now a thin compatibility shim around `thriftpy2 <https://github.com/Thriftpy/thriftpy2>`_.

Installing ``thriftpy`` installs the matching ``thriftpy2`` release and re-exports it under the historical ``thriftpy`` package name. Existing code that uses ``import thriftpy`` can keep that import while running on the maintained ``thriftpy2`` implementation.

For full documentation and usage details, use the thriftpy2 project:
https://github.com/Thriftpy/thriftpy2


Background
==========

For a while we did not have release access for the original ``thriftpy`` package, so active development moved to ``thriftpy2``. ``thriftpy2`` is the direct continuation of ``thriftpy``; apart from the package name, it provides the same project and implementation.

After seeing that some users still depend on the ``thriftpy`` name, we recovered the needed release access and turned ``thriftpy`` into a shim around ``thriftpy2``. Going forward, ``thriftpy`` and ``thriftpy2`` are released in sync with the same version number, and users can choose either package name.


Installation
============

.. code:: bash

    pip install thriftpy


Minimal Example
===============

Given a ``pingpong.thrift`` file:

::

    service PingPong {
        string ping(),
    }

Server:

.. code:: python

    import thriftpy
    from thriftpy.rpc import make_server

    pingpong_thrift = thriftpy.load("pingpong.thrift", module_name="pingpong_thrift")

    class Dispatcher(object):
        def ping(self):
            return "pong"

    server = make_server(pingpong_thrift.PingPong, Dispatcher(), "127.0.0.1", 6000)
    server.serve()

Client:

.. code:: python

    import thriftpy
    from thriftpy.rpc import make_client

    pingpong_thrift = thriftpy.load("pingpong.thrift", module_name="pingpong_thrift")

    client = make_client(pingpong_thrift.PingPong, "127.0.0.1", 6000)
    print(client.ping())
