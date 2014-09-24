from libc.stdlib cimport malloc, free
from libc.string cimport memcpy, memmove

from ..transport import TTransportException

DEF DEFAULT_BUFFER = 4096
DEF MIN_BUFFER_SZIE = 1024


cdef class TCyBuffer(object):
    def __cinit__(self, buf_size):
        self.buf = <char*>malloc(buf_size)
        self.buf_size = buf_size
        self.cur = 0
        self.data_size = 0

    def __dealloc__(self):
        if self.buf != NULL:
            free(self.buf)
            self.buf = NULL

    cdef void move_to_start(self):
        memmove(self.buf, self.buf + self.cur, self.data_size)
        self.cur = 0

    cdef void clean(self):
        self.cur = 0
        self.data_size = 0

    cdef int grow(self, int min_size):
        if min_size <= self.buf_size:
            return 0

        cdef int multiples = min_size / self.buf_size
        if min_size % self.buf_size != 0:
            multiples += 1

        cdef int new_size = self.buf_size * multiples
        cdef char *new_buf = <char*>malloc(new_size)
        if new_buf == NULL:
            return -1
        memcpy(new_buf + self.cur, self.buf + self.cur, self.data_size)
        free(self.buf)
        self.buf_size = new_size
        self.buf = new_buf
        return 0


cdef class TCyBufferedTransport(object):
    """binary reader/writer"""

    def __init__(self, trans, int buf_size=DEFAULT_BUFFER):
        if buf_size < MIN_BUFFER_SZIE:
            raise Exception("buffer too small")

        self.trans = trans
        self.rbuf = TCyBuffer(buf_size)
        self.wbuf = TCyBuffer(buf_size)

    def is_open(self):
        return self.trans.is_open()

    def open(self):
        return self.trans.open()

    def close(self):
        return self.trans.close()

    def write(self, bytes data):
        cdef int sz = len(data)
        return self.c_write(data, sz)

    def read(self, int sz):
        cdef char* out = <char*>malloc(sz)
        self.c_read(sz, out)
        try:
            return out[:sz]
        finally:
            free(out)

    def flush(self):
        return self.c_flush()

    cdef c_write(self, char* data, int sz):
        cdef int cap = self.wbuf.buf_size - self.wbuf.data_size

        if cap < sz:
            if sz > self.wbuf.buf_size:
                if self.wbuf.grow(sz) != 0:
                    raise MemoryError("grow write buffer fail")
            self.c_flush()

        memcpy(self.wbuf.buf + self.wbuf.data_size, data, sz)
        self.wbuf.data_size += sz

    cdef c_read(self, int sz, char* out):
        if sz > self.rbuf.buf_size:
            if self.rbuf.grow(sz) != 0:
                raise MemoryError("grow read buffer fail")

        cdef int cap, new_data_len
        cdef bytes new_data, ret_str

        if self.rbuf.data_size < sz:
            cap = self.rbuf.buf_size - self.rbuf.data_size
            new_data = self.trans.read(cap)
            new_data_len = len(new_data)

            while new_data_len < sz - self.rbuf.data_size:
                more = self.trans.read(cap - new_data_len)
                if len(more) <= 0:
                    raise TTransportException(
                        TTransportException.END_OF_FILE,
                        "End of file reading from transport")
                new_data += more
                new_data_len += len(more)

            if cap - self.rbuf.cur < new_data_len:
                self.rbuf.move_to_start()

            memcpy(self.rbuf.buf + self.rbuf.cur + self.rbuf.data_size,
                   <char*>new_data, new_data_len)
            self.rbuf.data_size += new_data_len

        memcpy(out, self.rbuf.buf + self.rbuf.cur, sz)

        self.rbuf.cur += sz
        self.rbuf.data_size -= sz

    cdef c_flush(self):
        cdef bytes data
        if self.wbuf.data_size > 0:
            data = self.wbuf.buf[:self.wbuf.data_size]
            self.trans.write(data)
            self.wbuf.clean()

    def getvalue(self):
        return self.trans.getvalue()


class TCyBufferedTransportFactory(object):
    def get_transport(self, trans):
        return TCyBufferedTransport(trans)
