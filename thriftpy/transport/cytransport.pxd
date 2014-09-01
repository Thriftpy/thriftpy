cdef class TCyBuffer(object):
    cdef char *buf
    cdef int cur, buf_size, data_size

    cdef void move_to_start(self)
    cdef void clean(self)
    cdef int grow(self, int min_size)


cdef class TCyBufferedTransport(object):
    cdef object trans
    cdef TCyBuffer rbuf, wbuf

    cdef c_read(self, int sz, char* out)
    cdef c_write(self, char* data, int sz)
    cdef c_flush(self)
