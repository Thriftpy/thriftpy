# -*- coding: utf-8 -*-

import time
import thriftpy

from thriftpy.rpc import make_server

sleep_thrift = thriftpy.load("sleep.thrift", module_name="sleep_thrift")


class Dispatcher(object):
    def sleep(self, seconds):
        print("I'm going to sleep %d seconds" % seconds)
        time.sleep(seconds)
        print("Sleep over!")


def main():
    server = make_server(sleep_thrift.Sleep, Dispatcher(),
                         '127.0.0.1', 6000)
    print("serving...")
    server.serve()


if __name__ == '__main__':
    main()
