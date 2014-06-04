# -*- coding: utf-8 -*-

import thriftpy
thriftpy.install_import_hook()

from thriftpy.protocol import TCyBinaryProtocolFactory
from thriftpy.rpc import make_server
import calc_thrift as calc


class Dispatcher(object):
    def add(self, a, b):
        print("add -> %s + %s" % (a, b))
        return a + b

    def sub(self, a, b):
        print("sub -> %s - %s" % (a, b))
        return a - b

    def mult(self, a, b):
        print("mult -> %s * %s" % (a, b))
        return a * b

    def div(self, a, b):
        print("div -> %s / %s" % (a, b))
        return a // b


def main():
    server = make_server(calc.Calculator, Dispatcher(), '127.0.0.1', 6000,
                         proto_factory=TCyBinaryProtocolFactory())
    print("serving...")
    server.serve()


if __name__ == '__main__':
    main()
