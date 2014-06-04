# -*- coding: utf-8 -*-

import thriftpy
thriftpy.install_import_hook()

from thriftpy.protocol import TCyBinaryProtocolFactory
from thriftpy.rpc import client_context
import calc_thrift as calc


def main():
    with client_context(calc.Calculator, '127.0.0.1', 6000,
                        proto_factory=TCyBinaryProtocolFactory()) as cal:
        a = cal.mult(5, 2)
        b = cal.sub(7, 3)
        c = cal.sub(6, 4)
        d = cal.mult(b, 10)
        e = cal.add(a, d)
        f = cal.div(e, c)
        print(f)


if __name__ == '__main__':
    main()
