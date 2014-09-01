from libc.stdlib cimport free, malloc
from libc.stdint cimport int16_t, int32_t, int64_t

from thriftpy.transport.cytransport cimport TCyBufferedTransport

cdef extern from "endian_port.h":
    int16_t htobe16(int16_t n)
    int32_t htobe32(int32_t n)
    int64_t htobe64(int64_t n)
    int16_t be16toh(int16_t n)
    int32_t be32toh(int32_t n)
    int64_t be64toh(int64_t n)

DEF VERSION_MASK = -65536
DEF VERSION_1 = -2147418112
DEF TYPE_MASK = 0x000000ff

DEF STACK_STRING_LEN = 4096

ctypedef enum TType:
    T_STOP = 0,
    T_VOID = 1,
    T_BOOL = 2,
    T_BYTE = 3,
    T_I08 = 3,
    T_I16 = 6,
    T_I32 = 8,
    T_U64 = 9,
    T_I64 = 10,
    T_DOUBLE = 4,
    T_STRING = 11,
    T_UTF7 = 11,
    T_NARY = 11
    T_STRUCT = 12,
    T_MAP = 13,
    T_SET = 14,
    T_LIST = 15,
    T_UTF8 = 16,
    T_UTF16 = 17

class ProtocolError(Exception):
    pass


cdef inline char read_i08(TCyBufferedTransport buf) except? -1:
    cdef char data
    buf.c_read(1, &data)
    return data


cdef inline int16_t read_i16(TCyBufferedTransport buf) except? -1:
    cdef char data[2]
    buf.c_read(2, data)
    return be16toh((<int16_t*>data)[0])


cdef inline int32_t read_i32(TCyBufferedTransport buf) except? -1:
    cdef char data[4]
    buf.c_read(4, data)
    return be32toh((<int32_t*>data)[0])


cdef inline int64_t read_i64(TCyBufferedTransport buf) except? -1:
    cdef char data[8]
    buf.c_read(8, data)
    return be64toh((<int64_t*>data)[0])


cdef inline int write_i08(TCyBufferedTransport buf, char val) except -1:
    buf.c_write(&val, 1)
    return 0


cdef inline int write_i16(TCyBufferedTransport buf, int16_t val) except -1:
    val = htobe16(val)
    buf.c_write(<char*>(&val), 2)
    return 0


cdef inline int write_i32(TCyBufferedTransport buf, int32_t val) except -1:
    val = htobe32(val)
    buf.c_write(<char*>(&val), 4)
    return 0


cdef inline int write_i64(TCyBufferedTransport buf, int64_t val) except -1:
    val = htobe64(val)
    buf.c_write(<char*>(&val), 8)
    return 0


cdef inline int write_double(TCyBufferedTransport buf, double val) except -1:
    cdef int64_t v = htobe64((<int64_t*>(&val))[0])
    buf.c_write(<char*>(&v), 8)
    return 0


cdef inline read_struct(TCyBufferedTransport buf, obj):
    cdef dict field_specs = obj.thrift_spec
    cdef int fid, i
    cdef TType field_type, orig_field_type, ttype
    cdef tuple field_spec
    cdef str name

    for i in range(len(field_specs) + 1):
        field_type = <TType>read_i08(buf)
        if field_type == T_STOP:
            break

        fid = read_i16(buf)
        if fid not in field_specs:
            raise ProtocolError("skip")

        field_spec = field_specs[fid]
        ttype = field_spec[0]
        if field_type != ttype:
            raise ProtocolError("Message Corrupt")

        name = field_spec[1]
        if len(field_spec) == 2:
            spec = None
        else:
            spec = field_spec[2]

        setattr(obj, name, c_read_val(buf, ttype, spec))

    return obj


cdef inline write_struct(TCyBufferedTransport buf, obj):
    cdef int fid, items_len, i
    cdef TType f_type
    cdef dict thrift_spec = obj.thrift_spec
    cdef tuple field_spec
    cdef str f_name

    for fid, field_spec in thrift_spec.items():
        f_type = field_spec[0]
        f_name = field_spec[1]
        if len(field_spec) == 2:
            container_spec = None
        else:
            container_spec = field_spec[2]

        v = getattr(obj, f_name)
        if v is None:
            continue

        write_i08(buf, f_type)
        write_i16(buf, fid)
        c_write_val(buf, f_type, v, container_spec)

    write_i08(buf, T_STOP)


cdef c_read_val(TCyBufferedTransport buf, TType ttype, spec=None):
    cdef int size
    cdef char* data
    cdef bytes py_data
    cdef int64_t n
    cdef TType v_type, k_type, orig_type, orig_key_type
    cdef char string_val[STACK_STRING_LEN]

    if ttype == T_BOOL:
        return bool(read_i08(buf))

    elif ttype == T_I08:
        return read_i08(buf)

    elif ttype == T_I16:
        return read_i16(buf)

    elif ttype == T_I32:
        return read_i32(buf)

    elif ttype == T_I64:
        return read_i64(buf)

    elif ttype == T_DOUBLE:
        n = read_i64(buf)
        return (<double*>(&n))[0]

    elif ttype == T_STRING:
        size = read_i32(buf)
        if size > STACK_STRING_LEN:
            data = <char*>malloc(size)
            buf.c_read(size, data)
            py_data = data[:size]
            free(data)
        else:
            buf.c_read(size, string_val)
            py_data = string_val[:size]
        try:
            return py_data.decode("utf-8")
        except UnicodeDecodeError:
            return py_data

    elif ttype == T_SET or ttype == T_LIST:
        if isinstance(spec, int):
            v_type = spec
            v_spec = None
        else:
            v_type = spec[0]
            v_spec = spec[1]

        orig_type = <TType>read_i08(buf)
        size = read_i32(buf)

        if orig_type != v_type:
            raise ProtocolError("Message Corrupt")

        return [c_read_val(buf, v_type, v_spec) for _ in range(size)]

    elif ttype == T_MAP:
        key = spec[0]
        if isinstance(key, int):
            k_type = key
            k_spec = None
        else:
            k_type = key[0]
            k_spec = key[1]

        value = spec[1]
        if isinstance(value, int):
            v_type = value
            v_spec = None
        else:
            v_type = value[0]
            v_spec = value[1]

        orig_key_type = <TType>read_i08(buf)
        orig_type = <TType>read_i08(buf)
        size = read_i32(buf)

        if orig_key_type != k_type or orig_type != v_type:
            raise ProtocolError("Message Corrupt")

        return {c_read_val(buf, k_type, k_spec): c_read_val(buf, v_type, v_spec)
                for _ in range(size)}

    elif ttype == T_STRUCT:
        return read_struct(buf, spec())


cdef c_write_val(TCyBufferedTransport buf, TType ttype, val, spec=None):
    cdef int val_len, i
    cdef TType e_type, v_type, k_type

    if ttype == T_BOOL:
        write_i08(buf, 1 if val else 0)

    elif ttype == T_I08:
        write_i08(buf, val)

    elif ttype == T_I16:
        write_i16(buf, val)

    elif ttype == T_I32:
        write_i32(buf, val)

    elif ttype == T_I64:
        write_i64(buf, val)

    elif ttype == T_DOUBLE:
        write_double(buf, val)

    elif ttype == T_STRING:
        if not isinstance(val, bytes):
            val = val.encode("utf-8")

        val_len = len(val)
        write_i32(buf, val_len)

        buf.c_write(<char*>val, val_len)

    elif ttype == T_SET or ttype == T_LIST:
        if isinstance(spec, int):
            e_type = spec
            e_spec = None
        else:
            e_type = spec[0]
            e_spec = spec[1]

        val_len = len(val)
        write_i08(buf, e_type)
        write_i32(buf, val_len)

        for i in range(val_len):
            c_write_val(buf, e_type, val[i], e_spec)

    elif ttype == T_MAP:
        key = spec[0]
        if isinstance(key, int):
            k_type = key
            k_spec = None
        else:
            k_type = key[0]
            k_spec = key[1]

        value = spec[1]
        if isinstance(value, int):
            v_type = value
            v_spec = None
        else:
            v_type = value[0]
            v_spec = value[1]

        val_len = len(val)

        write_i08(buf, k_type)
        write_i08(buf, v_type)
        write_i32(buf, val_len)

        for k, v in val.items():
            c_write_val(buf, k_type, k, k_spec)
            c_write_val(buf, v_type, v, v_spec)

    elif ttype == T_STRUCT:
        write_struct(buf, val)


def read_val(TCyBufferedTransport buf, TType ttype):
    return c_read_val(buf, ttype)


def write_val(TCyBufferedTransport buf, TType ttype, val, spec=None):
    c_write_val(buf, ttype, val, spec)


cdef class TCyBinaryProtocol(object):
    cdef public TCyBufferedTransport trans

    def __init__(self, trans):
        self.trans = trans

    def read_message_begin(self):
        cdef int32_t size, version, seqid
        cdef TType ttype

        size = read_i32(self.trans)
        version = size & VERSION_MASK
        if version != VERSION_1:
            raise ProtocolError('invalid version %d' % version)

        ttype = <TType>(size & TYPE_MASK)
        name = c_read_val(self.trans, T_STRING)
        seqid = read_i32(self.trans)

        return name, ttype, seqid

    def read_message_end(self):
        pass

    def write_message_begin(self, name, TType ttype, int32_t seqid):
        cdef int32_t version = VERSION_1 | ttype
        write_i32(self.trans, version)
        c_write_val(self.trans, T_STRING, name)
        write_i32(self.trans, seqid)

    def write_message_end(self):
        self.trans.c_flush()

    def read_struct(self, obj):
        return read_struct(self.trans, obj)

    def write_struct(self, obj):
        write_struct(self.trans, obj)


class TCyBinaryProtocolFactory(object):
    def get_protocol(self, trans):
        return TCyBinaryProtocol(trans)
