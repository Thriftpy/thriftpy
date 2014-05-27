# -*- coding: utf-8 -*-

from thriftpy.protocol import TCyBinaryProtocolFactory
from thriftpy.rpc import make_server
import tutorial_thrift as tutorial


class CalculatorHandler(object):
    def __init__(self):
        self.log = {}

    def ping(self):
        print('ping()')

    def add(self, num1, num2):
        print('add(%d,%d)' % (num1, num2))
        return num1 + num2

    def calculate(self, logid, work):
        print('calculate(%d, %r)' % (logid, work))

        if work.op == tutorial.Operation.ADD:
            val = work.num1 + work.num2
        elif work.op == tutorial.Operation.SUBTRACT:
            val = work.num1 - work.num2
        elif work.op == tutorial.Operation.MULTIPLY:
            val = work.num1 * work.num2
        elif work.op == tutorial.Operation.DIVIDE:
            if work.num2 == 0:
                x = tutorial.InvalidOperation()
                x.what = work.op
                x.why = 'Cannot divide by 0'
                raise x
            val = work.num1 / work.num2
        else:
            x = tutorial.InvalidOperation()
            x.what = work.op
            x.why = 'Invalid operation'
            raise x

        log = tutorial.SharedStruct()
        log.key = logid
        log.value = '%d' % (val)
        self.log[logid] = log

        return val

    def getStruct(self, key):
        print('getStruct(%d)' % (key))
        return self.log[key]

    def zip(self):
        print('zip()')


def main():
    server = make_server(
        tutorial.Calculator, CalculatorHandler(), '127.0.0.1', 6000,
        proto_factory=TCyBinaryProtocolFactory())
    print("serving...")
    server.serve()


if __name__ == '__main__':
    main()
