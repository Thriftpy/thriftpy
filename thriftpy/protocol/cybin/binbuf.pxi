from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from libc.stdint cimport *


cdef class Buffer(object):
    cdef byte *buf
    cdef int cur, buf_size, data_size

    def __init__(self, buf_size):
        self.buf = <byte*>malloc(buf_size)
        self.buf_size = buf_size
        self.cur = 0
        self.data_size = 0

    def __dealloc__(self):
        if self.buf != NULL:
            free(self.buf)

    cdef void move_to_start(self):
        if self.cur != 0 and self.data_size > 0:
            memcpy(self.buf, self.buf + self.cur, self.data_size)
            self.cur = 0

    cdef void clean(self):
        self.cur = 0
        self.data_size = 0


cdef class BinaryRW(object):
    '''binary reader/writer'''

    DEF DEFAULT_BUFFER = 4096
    cdef object trans
    cdef Buffer rbuf, wbuf

    def __init__(self, trans, int buf_size=DEFAULT_BUFFER):
        self.trans = trans
        self.buf_limit = buf_size
        self.rbuf = Buffer(buf_size)
        self.wbuf = Buffer(buf_size)

    cdef ensure_rbuf(self, int size):
        if size > self.rbuf.buf_size:
            return False

        cdef int buf_size = self.rbuf.data_size
        if buf_size == 0:
            self.rbuf.cur = 0
            self.rbuf.data_size = 0
        elif buf_size >= size:
            return True

        cdef int cap
        cdef bytes new_data
        if buf_size < size:
            cap = self.rbuf.buf_size - self.rbuf.data_size
            if cap < 256:
                self.rbuf.move_to_start()
            new_data = self.trans.read(cap)
            memcpy(self.rbuf.buf + self.rbuf.cur + self.rbuf.data_size,
                <byte*>new_data, len(new_data))
        return True

    cdef read_byte(self, byte *ret):
        self.ensure_rbuf(1)
        ret[0] = (self.rbuf.buf + self.rbuf.cur)[0]
        self.rbuf.cur += 1

    cdef read_int16(self, int16_t *ret):
        self.ensure_rbuf(2)
        ret[0] = (<int16_t*>(self.rbuf.buf + self.rbuf.cur))[0]
        self.rbuf.cur += 2

    cdef read_int32(self, int32_t *ret):
        self.ensure_rbuf(4)
        ret[0] = (<int32_t*>(self.rbuf.buf + self.rbuf.cur))[0]
        self.rbuf.cur += 4

    cdef read_int64(self, int64_t *ret):
        self.ensure_rbuf(8)
        ret[0] = (<int64_t*>(self.rbuf.buf + self.rbuf.cur))[0]
        self.rbuf.cur += 8

    cdef read_double(self, double *ret):
        self.ensure_rbuf(sizeof(double))
        ret[0] = (<double*>(self.rbuf.buf + self.rbuf.cur))[0]
        self.rbuf.cur += sizeof(double)

    cdef read_string(self):
        self.ensure_rbuf(4)
        cdef int32_t str_size = (<int32_t*>(self.rbuf.buf + self.rbuf.cur))[0]
        self.rbuf.cur += 4

        if str_size == 0:
            return ''
        self.ensure_rbuf(str_size)
        ret_str = (self.rbuf.buf + self.rbuf.cur)[:str_size].decode('utf8')
        self.rbuf.cur += str_size
        return ret_str

    cdef read_bytes(self, int size):
        pass

    cdef write_byte(self, int n):
        pass

    cdef write_int16(self, int n):
        pass

    cdef write_int32(self, int n):
        pass

    cdef write_int64(self, int n):
        pass

    cdef write_double(self, double n):
        pass

    cdef write_string(self, s):
        pass

    cdef write_bytes(self, bytes bs):
        pass
