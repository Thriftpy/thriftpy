from libc.stdlib cimport malloc, free
from libc.string cimport memcpy, memmove
from libc.stdint cimport *

from .transport import TTransportException


cdef class TCyBuffer(object):
    cdef byte *buf
    cdef int cur, buf_size, data_size

    def __cinit__(self, buf_size):
        self.buf = <byte*>malloc(buf_size)
        self.buf_size = buf_size
        self.cur = 0
        self.data_size = 0

    def __dealloc__(self):
        if self.buf != NULL:
            free(self.buf)
            self.buf = NULL

    cdef void move_to_start(self):
        if self.cur != 0 and self.data_size > 0:
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
        cdef byte *new_buf = <byte*>malloc(new_size)
        if new_buf == NULL:
            return -1
        memcpy(new_buf + self.cur, self.buf + self.cur, self.data_size)
        free(self.buf)
        self.buf_size = new_size
        self.buf = new_buf
        return 0


cdef class TCyBufferedTransport(object):
    """binary reader/writer"""

    DEF DEFAULT_BUFFER = 4096
    DEF MIN_BUFFER_SZIE = 1024

    cdef object trans
    cdef TCyBuffer rbuf, wbuf

    def __init__(self, trans, int buf_size=DEFAULT_BUFFER):
        if buf_size < MIN_BUFFER_SZIE:
            raise Exception('buffer too small')

        self.trans = trans
        self.rbuf = TCyBuffer(buf_size)
        self.wbuf = TCyBuffer(buf_size)

    cdef is_open(self):
        return self.trans.is_open()

    cdef open(self):
        return self.trans.open()

    cdef close(self):
        return self.trans.close()

    cdef write(self, buf):
        self.trans.write(buf)

    cdef ensure_rbuf(self, int size):
        if size > self.rbuf.buf_size:
            if self.rbuf.grow(size) != 0:
                raise MemoryError('grow read buffer fail')

        cdef int cap
        cdef bytes new_data

        if self.rbuf.data_size == 0:
            self.rbuf.cur = 0

        if self.rbuf.data_size < size:
            cap = self.rbuf.buf_size - self.rbuf.data_size
            new_data = self.trans.read(cap)
            new_data_len = len(new_data)

            while new_data_len < size - self.rbuf.data_size:
                chunk = self.trans.read(cap - new_data_len)
                new_data += chunk
                new_data_len += len(chunk)

                if len(chunk) == 0:
                    raise TTransportException(
                        TTransportException.END_OF_FILE,
                        "End of file reading from transport")

            # buf + buf_size >= buf + cur + data_size + new_data_len -->
            #   buf_size - data_size >= cur + new_data_len -->
            #     cap - cur >= new_data_len
            if cap - self.rbuf.cur < new_data_len:
                self.rbuf.move_to_start()
            memcpy(self.rbuf.buf + self.rbuf.cur + self.rbuf.data_size,
                <byte*>new_data, new_data_len)
            self.rbuf.data_size += new_data_len

    cdef read_byte(self, byte *ret):
        self.ensure_rbuf(1)
        ret[0] = (self.rbuf.buf + self.rbuf.cur)[0]
        self.rbuf.cur += 1
        self.rbuf.data_size -= 1

    cdef read_int16(self, int16_t *ret):
        self.ensure_rbuf(2)
        ret[0] = be16toh((<int16_t*>(self.rbuf.buf + self.rbuf.cur))[0])
        self.rbuf.cur += 2
        self.rbuf.data_size -= 2

    cdef read_int32(self, int32_t *ret):
        self.ensure_rbuf(4)
        ret[0] = be32toh((<int32_t*>(self.rbuf.buf + self.rbuf.cur))[0])
        self.rbuf.cur += 4
        self.rbuf.data_size -= 4

    cdef read_int64(self, int64_t *ret):
        self.ensure_rbuf(8)
        ret[0] = be64toh((<int64_t*>(self.rbuf.buf + self.rbuf.cur))[0])
        self.rbuf.cur += 8
        self.rbuf.data_size -= 8

    cdef read_double(self, double *ret):
        self.ensure_rbuf(sizeof(double))
        cdef int64_t n = be64toh((<int64_t*>(self.rbuf.buf + self.rbuf.cur))[0])
        ret[0] = (<double*>(&n))[0]
        self.rbuf.cur += sizeof(double)
        self.rbuf.data_size -= sizeof(double)

    cdef read_string(self):
        self.ensure_rbuf(4)
        cdef int32_t str_size = be32toh((<int32_t*>(self.rbuf.buf + self.rbuf.cur))[0])
        self.rbuf.cur += 4
        self.rbuf.data_size -= 4

        if str_size == 0:
            return ''
        self.ensure_rbuf(str_size)
        ret_str = (self.rbuf.buf + self.rbuf.cur)[:str_size].decode('utf8')
        self.rbuf.cur += str_size
        self.rbuf.data_size -= str_size
        return ret_str

    cdef read_bytes(self, int size):
        self.ensure_rbuf(size)
        cdef bytes ret_bs = (self.rbuf.buf + self.rbuf.cur)[:size]
        self.rbuf.cur += size
        self.rbuf.data_size -= size
        return ret_bs

    cdef read_skip(self, int size):
        self.ensure_rbuf(size)
        self.rbuf.cur += size
        self.rbuf.data_size -= size

    cdef ensure_wbuf(self, int size):
        cdef int cap = self.wbuf.buf_size - self.wbuf.data_size

        if cap < size:
            if size > self.wbuf.buf_size:
                if self.wbuf.grow(size) != 0:
                    raise MemoryError('grow write buffer fail')
            self.write_flush()

    cdef write_byte(self, byte n):
        self.ensure_wbuf(1)
        (self.wbuf.buf + self.wbuf.data_size)[0] = n
        self.wbuf.data_size += 1

    cdef write_int16(self, int16_t n):
        self.ensure_wbuf(2)
        (<int16_t*>(self.wbuf.buf + self.wbuf.data_size))[0] = htobe16(n)
        self.wbuf.data_size += 2

    cdef write_int32(self, int32_t n):
        self.ensure_wbuf(4)
        (<int32_t*>(self.wbuf.buf + self.wbuf.data_size))[0] = htobe32(n)
        self.wbuf.data_size += 4

    cdef write_int64(self, int64_t n):
        self.ensure_wbuf(8)
        (<int64_t*>(self.wbuf.buf + self.wbuf.data_size))[0] = htobe64(n)
        self.wbuf.data_size += 8

    cdef write_double(self, double n):
        self.ensure_wbuf(8)
        cdef int64_t *n64 = <int64_t*>(&n)
        (<int64_t*>(self.wbuf.buf + self.wbuf.data_size))[0] = htobe64(n64[0])
        self.wbuf.data_size += 8

    cdef write_string(self, s):
        cdef bytes bs
        if isinstance(s, bytes):
            bs = s
        else:
            bs = s.encode('utf8')

        cdef int size = len(bs)
        self.ensure_wbuf(4)
        (<int32_t*>(self.wbuf.buf + self.wbuf.data_size))[0] = htobe32(size)
        self.wbuf.data_size += 4

        self.ensure_wbuf(size)
        memcpy(self.wbuf.buf + self.wbuf.data_size, <byte*>bs, size)
        self.wbuf.data_size += size

    cdef write_bytes(self, bytes bs):
        cdef int size = len(bs)
        self.ensure_wbuf(size)
        memcpy(self.wbuf.buf + self.wbuf.data_size, <byte*>bs, size)
        self.wbuf.data_size += size

    cdef write_flush(self):
        cdef bytes data
        if self.wbuf.data_size > 0:
            data = self.wbuf.buf[:self.wbuf.data_size]
            self.trans.write(data)
            self.wbuf.clean()


class TCyBufferedTransportFactory(object):
    def get_transport(self, trans):
        return TCyBufferedTransport(trans)
