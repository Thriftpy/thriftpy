# -*- coding: utf-8 -*-
import logging

from example.idl import shared, tutorial


logger = logging.getLogger(__name__)


class CalculatorHandler(object):

    def __init__(self):
        self.log = {}

    def ping(self):
        logger.info('ping()')

    def add(self, num1, num2):
        logger.info('add(%d, %d)', num1, num2)
        return num1 + num2

    def calculate(self, logid, work):
        logger.info('calculate(%d, %r)', logid, work)

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

        log = shared.SharedStruct()
        log.key = logid
        log.value = '%d' % (val)
        self.log[logid] = log

        return val

    def getStruct(self, key):
        logger.info('getStruct(%d)', key)
        return self.log[key]

    def zip(self):
        logger.info('zip()')
