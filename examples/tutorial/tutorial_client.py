# -*- coding: utf-8 -*-

import thriftpy

from thriftpy.rpc import client_context

tutorial_thrift = thriftpy.load("tutorial.thrift",
                                module_name="tutorial_thrift")


def main():
    with client_context(tutorial_thrift.Calculator,
                        '127.0.0.1', 6000) as client:
        client.ping()
        print("ping()")

        total = client.add(1, 1)
        print('1+1=%d' % (total))

        work = tutorial_thrift.Work()
        work.op = tutorial_thrift.Operation.DIVIDE
        work.num1 = 1
        work.num2 = 0

        try:
            client.calculate(1, work)
            print('Whoa? You know how to divide by zero?')
        except tutorial_thrift.InvalidOperation as io:
            print('InvalidOperation: %r' % io)

        work.op = tutorial_thrift.Operation.SUBTRACT
        work.num1 = 15
        work.num2 = 10

        diff = client.calculate(1, work)
        print('15-10=%d' % (diff))

        log = client.getStruct(1)
        print('Check log: %s' % (log.value))


if __name__ == '__main__':
    main()
