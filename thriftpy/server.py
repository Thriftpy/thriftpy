# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import threading

from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.transport import (
    TBufferedTransportFactory,
    TTransportException
)

from multiprocessing import  Process, Value, Condition, reduction

logger = logging.getLogger(__name__)


class TServer(object):
    def __init__(self, processor, trans,
                 itrans_factory=None, iprot_factory=None,
                 otrans_factory=None, oprot_factory=None):
        self.processor = processor
        self.trans = trans

        self.itrans_factory = itrans_factory or TBufferedTransportFactory()
        self.iprot_factory = iprot_factory or TBinaryProtocolFactory()
        self.otrans_factory = otrans_factory or self.itrans_factory
        self.oprot_factory = oprot_factory or self.iprot_factory

    def serve(self):
        pass

    def close(self):
        pass


class TSimpleServer(TServer):
    """Simple single-threaded server that just pumps around one transport."""

    def __init__(self, *args):
        TServer.__init__(self, *args)
        self.closed = False

    def serve(self):
        self.trans.listen()
        while not self.closed:
            client = self.trans.accept()
            itrans = self.itrans_factory.get_transport(client)
            otrans = self.otrans_factory.get_transport(client)
            iprot = self.iprot_factory.get_protocol(itrans)
            oprot = self.oprot_factory.get_protocol(otrans)
            try:
                while not self.closed:
                    self.processor.process(iprot, oprot)
            except TTransportException:
                pass
            except Exception as x:
                logger.exception(x)

            itrans.close()
            otrans.close()

    def close(self):
        self.closed = True


class TThreadedServer(TServer):
    """Threaded server that spawns a new thread per each connection."""

    def __init__(self, *args, **kwargs):
        self.daemon = kwargs.pop("daemon", False)
        TServer.__init__(self, *args, **kwargs)
        self.closed = False

    def serve(self):
        self.trans.listen()
        while not self.closed:
            try:
                client = self.trans.accept()
                t = threading.Thread(target=self.handle, args=(client,))
                t.setDaemon(self.daemon)
                t.start()
            except KeyboardInterrupt:
                raise
            except Exception as x:
                logger.exception(x)

    def handle(self, client):
        itrans = self.itrans_factory.get_transport(client)
        otrans = self.otrans_factory.get_transport(client)
        iprot = self.iprot_factory.get_protocol(itrans)
        oprot = self.oprot_factory.get_protocol(otrans)
        try:
            while True:
                self.processor.process(iprot, oprot)
        except TTransportException:
            pass
        except Exception as x:
            logger.exception(x)

        itrans.close()
        otrans.close()

    def close(self):
        self.closed = True


class TProcessPoolServer(TServer):
    """Server with a fixed size pool of worker subprocesses to service requests

    Note that if you need shared state between the handlers - it's up to you!
    Written by Dvir Volk, doat.com
    """
    def __init__(self, *args, **kwargs):
        self.daemon = kwargs.pop("daemon", False)
        TServer.__init__(self, *args, **kwargs)
        self.closed = False

        self.numWorkers = 1
        self.workers = []
        self.isRunning = Value('b', False)
        self.stopCondition = Condition()
        self.postForkCallback = None

    def setPostForkCallback(self, callback):
        if not callable(callback):
            raise TypeError("This is not a callback!")
        self.postForkCallback = callback

    def setNumWorkers(self, num):
        """Set the number of worker threads that should be created"""
        self.numWorkers = num

    def workerProcess(self):
        """Loop getting clients from the shared queue and process them"""
        if self.postForkCallback:
            self.postForkCallback()

        while self.isRunning.value:
            try:
                client = self.trans.accept()
                if not client:
                  continue
                self.serveClient(client)
            except (KeyboardInterrupt, SystemExit):
                return 0
            except Exception as x:
                logger.exception(x)

    def serveClient(self, client):
        """Process input/output from a client for as long as possible"""

        itrans = self.itrans_factory.get_transport(client)
        otrans = self.otrans_factory.get_transport(client)
        iprot = self.iprot_factory.get_protocol(itrans)
        oprot = self.oprot_factory.get_protocol(otrans)

        try:
            while True:
                self.processor.process(iprot, oprot)
        except TTransportException as tx:
            pass
        except Exception as x:
            logger.exception(x)

        itrans.close()
        otrans.close()

    def serve(self):
        """Start workers and put into queue"""
        # this is a shared state that can tell the workers to exit when False
        self.isRunning.value = True

        # first bind and listen to the port
        self.trans.listen()

        # fork the children
        for i in range(self.numWorkers):
            try:
                w = Process(target=self.workerProcess)
                w.daemon = True
                w.start()
                self.workers.append(w)
            except Exception as x:
                logger.exception(x)

        # wait until the condition is set by stop()
        while True:
            self.stopCondition.acquire()
            try:
                self.stopCondition.wait()
                break
            except (SystemExit, KeyboardInterrupt):
                break
            except Exception as x:
                logger.exception(x)

        self.isRunning.value = False

    def stop(self):
        self.isRunning.value = False
        self.stopCondition.acquire()
        self.stopCondition.notify()
        self.stopCondition.release()

    def close(self):
        self.closed = True
