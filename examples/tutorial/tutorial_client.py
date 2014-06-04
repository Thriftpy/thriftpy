# -*- coding: utf-8 -*-

import thriftpy
thriftpy.install_import_hook()

from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.rpc import client_context
import tutorial_thrift as tutorial


def main():
    with client_context(tutorial.Calculator, '127.0.0.1', 6000,
                        proto_factory=TBinaryProtocolFactory()) as client:
        client.ping()
        print("ping()")

        total = client.add(1, 1)
        print('1+1=%d' % (total))

        work = tutorial.Work()
        work.op = tutorial.Operation.DIVIDE
        work.num1 = 1
        work.num2 = 0

        try:
            client.calculate(1, work)
            print('Whoa? You know how to divide by zero?')
        except tutorial.InvalidOperation as io:
            print('InvalidOperation: %r' % io)

        work.op = tutorial.Operation.SUBTRACT
        work.num1 = 15
        work.num2 = 10

        diff = client.calculate(1, work)
        print('15-10=%d' % (diff))

        log = client.getStruct(1)
        print('Check log: %s' % (log.value))


if __name__ == '__main__':
    main()
