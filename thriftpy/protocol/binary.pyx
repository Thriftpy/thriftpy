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

cdef:
    int8_t int8_sz = sizeof(int8_t)
    int8_t int16_sz = sizeof(int16_t)
    int8_t int32_sz = sizeof(int32_t)


cdef void _revert_memcpy(char* buf, void* x, int sz):
    cdef:
        int i
        char* s = <char*> x

    for i in range(sz):
        buf[i] = s[sz-1-i]


cdef void _write_num(char* buf, num val):
    _revert_memcpy(buf, &val, sizeof(val))

cdef void _write_string(char* buf, bytes val):
    cdef:
        int32_t val_len = len(val)
    _revert_memcpy(buf, &val_len, int32_sz)
    memcpy(buf + int32_sz, <char*>val, val_len)

cdef bytes _pack_num(num val):
    cdef:
        int sz = sizeof(val)
        char* buf = <char*>malloc(sz)
    _revert_memcpy(buf, &val, sz)
    return buf[:sz]

cpdef bytes pack_i8(int8_t val):
    return _pack_num(val)

cpdef bytes pack_i16(int16_t val):
    return _pack_num(val)

cpdef bytes pack_i32(int32_t val):
    return _pack_num(val)

cpdef bytes pack_i64(int64_t val):
    return _pack_num(val)

cpdef bytes pack_bool(int8_t bool_):
    if bool_:
        return pack_i8(1)
    else:
        return pack_i8(0)

cpdef bytes pack_double(double val):
    return _pack_num(val)

cpdef bytes pack_string(bytes val):
    cdef:
        int val_len = len(val)
        int sz = sizeof(val_len)
    cdef char* buf = <char*>malloc(sz + val_len)
    _write_string(buf, val)
    return buf[:sz + val_len]

cpdef write_field_begin(outbuf, int8_t ttype, int16_t fid):
    cdef char* buf = <char*>malloc(int8_sz + int16_sz)
    _write_num(buf, ttype)
    _write_num(buf + int8_sz, fid)
    outbuf.write(buf[:int8_sz + int16_sz])

cpdef write_field_stop(outbuf):
    outbuf.write(pack_i8(STOP))

cpdef write_list_begin(outbuf, int8_t e_type, int32_t size):
    cdef char* buf = <char*>malloc(int8_sz + int32_sz)
    _write_num(buf, e_type)
    _write_num(buf + int8_sz, size)
    outbuf.write(buf[:int8_sz + int32_sz])

cpdef write_map_begin(outbuf, int8_t k_type, int8_t v_type, int32_t size):
    cdef char* buf = <char*>malloc(int8_sz * 2 + int32_sz)
    _write_num(buf, k_type)
    _write_num(buf + int8_sz, v_type)
    _write_num(buf + int8_sz * 2, size)
    outbuf.write(buf[:int8_sz * 2 + int32_sz])

cpdef write_output(outbuf, int8_t ttype, val, spec=None):
    cdef:
        int8_t e_type, k_type, v_type
        int32_t i, val_len
        bytes res = b''
        tuple e_spec
        str e_name

    if ttype == BOOL:
        if val:
            outbuf.write(pack_i8(1))
        else:
            outbuf.write(pack_i8(0))

    elif ttype == BYTE:
        outbuf.write(pack_i8(val))

    elif ttype == I16:
        outbuf.write(pack_i16(val))

    elif ttype == I32:
        outbuf.write(pack_i32(val))

    elif ttype == I64:
        outbuf.write(pack_i64(val))

    elif ttype == DOUBLE:
        outbuf.write(pack_double(val))

    elif ttype == STRING:
        outbuf.write(pack_string(val))

    elif ttype == SET or ttype == LIST:
        if isinstance(spec, tuple):
            e_type, t_spec = spec[0], spec[1]
        else:
            e_type, t_spec = spec, None

        val_len = len(val)
        write_list_begin(outbuf, e_type, val_len)
        for i in range(val_len):
            write_output(outbuf, e_type, val[i], t_spec)

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

        write_map_begin(outbuf, k_type, v_type, len(val))
        for k in iter(val):
            write_output(outbuf, k_type, k, k_spec) 
            write_output(outbuf, v_type, val[k], v_spec)

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

            write_field_begin(outbuf, e_type, i)
            write_output(outbuf, e_type, v, e_container_spec)
        write_field_stop(outbuf)

cpdef write_message_begin(outbuf, bytes name, int8_t ttype, int32_t seqid):
    cdef char* buf = <char*>malloc(len(name) + int8_sz + int32_sz * 2)
    _write_string(buf, name)
    _write_num(buf + int32_sz + len(name), ttype)
    _write_num(buf + int32_sz + len(name) + int8_sz, seqid)
    outbuf.write(buf[:len(name) + int8_sz + int32_sz * 2])
