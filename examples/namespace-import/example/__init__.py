#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import pkg_resources as pkg
from functools import partial

import thriftpy

# Mount namespace at the very top level package
thriftpy.mount_namespace('example.idl', pkg.resource_filename(__name__, 'idl'))

from thriftpy import rpc
from thriftpy.protocol import TCyBinaryProtocolFactory
from thriftpy.transport import TCyBufferedTransportFactory

from example import handler
from example.idl import tutorial


__all__ = ['client', 'server']


logging.basicConfig(
    level=logging.DEBUG, format='[%(levelname)s][%(asctime)s] %(message)s')

HOST = '127.0.0.1'
PORT = 9999


server = rpc.make_server(
    tutorial.Calculator,
    handler.CalculatorHandler(),
    host=HOST,
    port=PORT,
    proto_factory=TCyBinaryProtocolFactory(),
    trans_factory=TCyBufferedTransportFactory(),
)


client = partial(
    rpc.client_context,
    tutorial.Calculator,
    host=HOST,
    port=PORT,
    proto_factory=TCyBinaryProtocolFactory(),
    trans_factory=TCyBufferedTransportFactory(),
)
