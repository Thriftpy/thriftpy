from libc.stdlib cimport malloc, free


cdef class BinaryProtocol(object):
    DEF DEFAULT_BUFFER = 4096
    cdef BinaryRW buf

    def __init__(self, trans, int buf_size=DEFAULT_BUFFER):
        self.buf = BinaryRW(trans, buf_size)

    def read_message_begin(self):
        pass

    def read_message_end(self):
        pass

    def write_message_begin(self, name, ttype, seqid):
        pass

    def write_message_end(self):
        pass

    def read_struct(self, obj):
        pass

    def write_struct(self, obj):
        pass
