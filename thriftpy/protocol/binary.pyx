from libc.stdlib cimport malloc
from libc.string cimport memcmp, memcpy
from libc.stdint cimport (
    int8_t,
    int16_t,
    int32_t,
    int64_t,
)

ctypedef fused num:
    int8_t
    int16_t
    int32_t
    int64_t
    double


cdef public enum TType:
    STOP = 0
    VOID = 1
    BOOL = 2
    BYTE = 3
    I08 = 3
    DOUBLE = 4
    I16 = 6
    I32 = 8
    I64 = 10
    STRING = 11
    UTF7 = 11
    STRUCT = 12
    MAP = 13
    SET = 14
    LIST = 15
    UTF8 = 16
    UTF16 = 17


cdef:
    int VERSION_MASK = 0xffff0000
    int VERSION_1 = 0x80010000
    int TYPE_MASK = 0x000000ff


cdef void _revert_memcpy(char* outbuf, void* x, int sz):
    cdef:
        int i
        char* s = <char*> x

    for i in range(sz):
        outbuf[i] = s[sz-1-i]


cdef bytes _write_num(num val):
    cdef int32_t sz = sizeof(val)
    cdef char* outbuf = <char*>malloc(sz)
    _revert_memcpy(outbuf, &val, sz)
    return outbuf[:sz]

cpdef bytes write_i8(int8_t val):
    return _write_num(val)

cpdef bytes write_i16(int16_t val):
    return _write_num(val)

cpdef bytes write_i32(int32_t val):
    return _write_num(val)

cpdef bytes write_i64(int64_t val):
    return _write_num(val)

cpdef bytes write_bool(int8_t bool_):
    if bool_:
        return write_i8(1)
    else:
        return write_i8(0)

cpdef bytes write_double(double val):
    return _write_num(val)

cpdef bytes write_string(bytes val):
    cdef:
        int32_t sz = sizeof(int32_t)
        int32_t val_len = len(val)
        cdef char* outbuf = <char*>malloc(sz + val_len)
    _revert_memcpy(outbuf, &val_len, sz)
    memcpy(outbuf + sz, <char*>val, val_len)
    return outbuf[:sz + val_len]

cdef bytes write_field_begin(TType ttype, int32_t fid):
    return write_i8(ttype) + write_i32(fid)

cdef bytes write_field_stop():
    return write_i8(STOP)

cdef bytes write_list_begin(TType e_type, int32_t size):
    return write_i8(e_type) + write_i32(size)

cdef bytes write_map_begin(TType k_type, TType v_type, int32_t size):
    return write_i8(k_type) + write_i8(v_type) + write_i32(size)

cpdef bytes write_output(TType ttype, val, spec=None):
    cdef:
        TType e_type, k_type, v_type
        int32_t i, val_len
        bytes res = b''
        tuple e_spec
        str e_name

    if ttype == BOOL:
        if val:
            return write_i8(1)
        else:
            return write_i8(0)

    elif ttype == BYTE:
        return write_i8(val)

    elif ttype == DOUBLE:
        return write_double(val)

    elif ttype == I16:
        return write_i16(val)

    elif ttype == I32:
        return write_i32(val)

    elif ttype == I64:
        return write_i64(val)

    elif ttype == STRING:
        return write_string(val)

    elif ttype == SET or ttype == LIST:
        if isinstance(spec, tuple):
            e_type, t_spec = spec[0], spec[1]
        else:
            e_type, t_spec = spec, None

        val_len = len(val)
        res = write_list_begin(e_type, val_len)
        for i in range(val_len):
            res += write_output(e_type, val[i], t_spec)
        return res

    elif ttype == MAP:
        if isinstance(spec[0], int):
            k_type = spec[0]
            k_spec = None
        else:
            k_type, k_spec = spec[0]

        if isinstance(spec[1], int):
            v_type = spec[1]
            v_spec = None
        else:
            v_type, v_spec = spec[1]

        res = write_map_begin(k_type, v_type, len(val))
        for k in iter(val):
            v = val[k]
            res += write_output(k_type, k, k_spec) 
            res += write_output(v_type, v, v_spec)
        return res

    elif ttype == STRUCT:
        for i in iter(spec):
            e_spec = spec[i]
            if len(e_spec) == 2:
                e_type, e_name = e_spec
                e_container_spec = None
            else:
                e_type, e_name, e_container_spec = e_spec

            v = getattr(val, e_name)
            if v is None:
                continue

            res += write_field_begin(e_type, i)
            res += write_output(e_type, v, e_container_spec)
        res += write_field_stop()
        return res

cpdef bytes write_message_begin(bytes name, TType ttype, int32_t seqid):
    return write_string(name) + write_i8(ttype) + write_i32(seqid)
