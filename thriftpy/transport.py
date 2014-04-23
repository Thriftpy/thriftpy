# -*- coding: utf-8 -*-

import errno
import os
import socket
import sys

from io import BytesIO

from .thrift import TException


class TTransportBase(object):
    """Base class for Thrift transport layer."""

    def readAll(self, sz):
        buff = b''
        have = 0
        while (have < sz):
            chunk = self.read(sz - have)
            have += len(chunk)
            buff += chunk

            if len(chunk) == 0:
                raise EOFError()

        return buff


class TTransportException(TException):
    """Custom Transport Exception class"""

    UNKNOWN = 0
    NOT_OPEN = 1
    ALREADY_OPEN = 2
    TIMED_OUT = 3
    END_OF_FILE = 4

    def __init__(self, type=UNKNOWN, message=None):
        TException.__init__(self, message)
        self.type = type


class TMemoryBuffer(TTransportBase):
    """Wraps a BytesIO object as a TTransport.

    NOTE: Unlike the C++ version of this class, you cannot write to it
          then immediately read from it.
          If you want to read from a TMemoryBuffer, you must either pass
          a string to the constructor.
    TODO(dreiss): Make this work like the C++ version.
    """

    def __init__(self, value=None):
        """value -- a value to read from for stringio

        If value is set, this will be a transport for reading,
        otherwise, it is for writing
        """
        self._buffer = BytesIO(value) if value is not None else BytesIO()

    def isOpen(self):
        return not self._buffer.closed

    def open(self):
        pass

    def close(self):
        self._buffer.close()

    def read(self, sz):
        return self._buffer.read(sz)

    def write(self, buf):
        self._buffer.write(buf)

    def flush(self):
        pass

    def getvalue(self):
        return self._buffer.getvalue()


class TBufferedTransport(TTransportBase):
    """Class that wraps another transport and buffers its I/O.

    The implementation uses a (configurable) fixed-size read buffer
    but buffers all writes until a flush is performed.
    """
    DEFAULT_BUFFER = 4096

    def __init__(self, trans, rbuf_size=DEFAULT_BUFFER):
        self.__trans = trans
        self.__wbuf = BytesIO()
        self.__rbuf = BytesIO(b"")
        self.__rbuf_size = rbuf_size

    def isOpen(self):
        return self.__trans.isOpen()

    def open(self):
        return self.__trans.open()

    def close(self):
        return self.__trans.close()

    def read(self, sz):
        ret = self.__rbuf.read(sz)
        if len(ret) != 0:
            return ret

        self.__rbuf = BytesIO(self.__trans.read(max(sz, self.__rbuf_size)))
        return self.__rbuf.read(sz)

    def write(self, buf):
        self.__wbuf.write(buf)

    def flush(self):
        out = self.__wbuf.getvalue()
        # reset wbuf before write/flush to preserve state on underlying failure
        self.__wbuf = BytesIO()
        self.__trans.write(out)
        self.__trans.flush()


class TBufferedTransportFactory(object):
    def get_transport(self, trans):
        return TBufferedTransport(trans)


class TSocketBase(TTransportBase):
    def _resolveAddr(self):
        if self._unix_socket is not None:
            return [(socket.AF_UNIX, socket.SOCK_STREAM, None, None,
                     self._unix_socket)]
        else:
            return socket.getaddrinfo(
                self.host,
                self.port,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
                0,
                socket.AI_PASSIVE | socket.AI_ADDRCONFIG)

    def close(self):
        if self.handle:
            self.handle.close()
            self.handle = None


class TSocket(TSocketBase):
    """Socket implementation of TTransport base."""

    def __init__(self, host='localhost', port=9090, unix_socket=None):
        """Initialize a TSocket

        @param host(str)    The host to connect to.
        @param port(int)    The (TCP) port to connect to.
        @param unix_socket(str)  The filename of a unix socket to connect to.
                                 (host and port will be ignored.)
        """
        self.host = host
        self.port = port
        self.handle = None
        self._unix_socket = unix_socket
        self._timeout = None

    def setHandle(self, h):
        self.handle = h

    def isOpen(self):
        return self.handle is not None

    def setTimeout(self, ms):
        if ms is None:
            self._timeout = None
        else:
            self._timeout = ms / 1000.0

        if self.handle is not None:
            self.handle.settimeout(self._timeout)

    def open(self):
        try:
            res0 = self._resolveAddr()
            for res in res0:
                self.handle = socket.socket(res[0], res[1])
                self.handle.settimeout(self._timeout)
                try:
                    self.handle.connect(res[4])
                except socket.error as e:
                    if res is not res0[-1]:
                        continue
                    else:
                        raise e
                break
        except socket.error as e:
            if self._unix_socket:
                message = 'Could not connect to socket %s' % self._unix_socket
            else:
                message = 'Could not connect to %s:%d' % (self.host, self.port)
            raise TTransportException(type=TTransportException.NOT_OPEN,
                                      message=message)

    def read(self, sz):
        try:
            buff = self.handle.recv(sz)
        except socket.error as e:
            if (e.args[0] == errno.ECONNRESET and
                    (sys.platform == 'darwin' or
                     sys.platform.startswith('freebsd'))):
                # freebsd and Mach don't follow POSIX semantic of recv
                # and fail with ECONNRESET if peer performed shutdown.
                # See corresponding comment and code in TSocket::read()
                # in lib/cpp/src/transport/TSocket.cpp.
                self.close()
                # Trigger the check to raise the END_OF_FILE exception below.
                buff = ''
            else:
                raise
        if len(buff) == 0:
            raise TTransportException(type=TTransportException.END_OF_FILE,
                                      message='TSocket read 0 bytes')
        return buff

    def write(self, buff):
        if not self.handle:
            raise TTransportException(type=TTransportException.NOT_OPEN,
                                      message='Transport not open')
        sent = 0
        have = len(buff)
        while sent < have:
            plus = self.handle.send(buff)
            if plus == 0:
                raise TTransportException(type=TTransportException.END_OF_FILE,
                                          message='TSocket sent 0 bytes')
            sent += plus
            buff = buff[plus:]

    def flush(self):
        pass


class TServerSocket(TSocketBase):
    """Socket implementation of TServerTransport base."""

    def __init__(self, host=None, port=9090, unix_socket=None,
                 socket_family=socket.AF_UNSPEC):
        self.host = host
        self.port = port
        self._unix_socket = unix_socket
        self._socket_family = socket_family
        self.handle = None

    def listen(self):
        res0 = self._resolveAddr()
        socket_family = self._socket_family == socket.AF_UNSPEC and (
            socket.AF_INET6 or self._socket_family)
        for res in res0:
            if res[0] is socket_family or res is res0[-1]:
                break

        # We need remove the old unix socket if the file exists and
        # nobody is listening on it.
        if self._unix_socket:
            tmp = socket.socket(res[0], res[1])
            try:
                tmp.connect(res[4])
            except socket.error as err:
                eno, message = err.args
                if eno == errno.ECONNREFUSED:
                    os.unlink(res[4])

        self.handle = socket.socket(res[0], res[1])
        self.handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(self.handle, 'settimeout'):
            self.handle.settimeout(None)
        self.handle.bind(res[4])
        self.handle.listen(128)

    def accept(self):
        client, addr = self.handle.accept()
        result = TSocket()
        result.setHandle(client)
        return result
