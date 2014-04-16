import struct

from libc.stdint cimport (
    int8_t,
    int16_t,
    int32_t,
    int64_t,
)

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


cdef int VERSION_MASK = 0xffff0000
cdef int VERSION_1 = 0x80010000
cdef int TYPE_MASK = 0x000000ff


cdef bytes write_int8(int8_t val):
    return struct.pack("!b", val)

cdef bytes write_i16(int16_t val):
    return struct.pack("!h", val)

cdef bytes write_i32(int32_t val):
    return struct.pack("!i", val)

cdef bytes write_i64(int64_t val):
    return struct.pack("!q", val)

cdef bytes write_bool(int8_t bool_):
    if bool_:
        return write_int8(1)
    else:
        return write_int8(0)

cdef bytes write_double(double val):
    return struct.pack("!d", val)

cdef bytes write_string(bytes val):
    cdef int32_t length = len(val)
    cdef str fmt
    fmt = "!i%ds" % length
    return struct.pack(fmt, length, val)

cdef bytes write_field_begin(TType ttype, int32_t fid):
    return struct.pack("!bh", ttype, fid)

cdef bytes write_field_stop():
    return struct.pack("!b", STOP)

cdef bytes write_list_begin(TType e_type, int32_t size):
    return struct.pack("!bi", e_type, size)

cdef bytes write_map_begin(TType k_type, TType v_type, int32_t size):
    return struct.pack("!bbi", k_type, v_type, size)

cdef tuple write_prepare(TType ttype, val, spec):
    cdef TType e_type, k_type, v_type
    cdef int32_t i, val_len
    cdef tuple e_spec
    cdef str e_name

    cdef str _fmt
    cdef str fmt = ''
    cdef list vals = []

    if ttype == BOOL:
        fmt += 'b'
        if val:
            vals.append(1)
        else:
            vals.append(0)

    elif ttype == BYTE:
        fmt += 'b'
        vals.append(val)

    elif ttype == I16:
        fmt += 'd'
        vals.append(val)

    elif ttype == I32:
        fmt += 'i'
        vals.append(val)

    elif ttype == I64:
        fmt += 'q'
        vals.append(val)

    elif ttype == DOUBLE:
        fmt += 'd'
        vals.append(val)

    elif ttype == STRING:
        val_len = len(val)
        fmt += "i%ss" % val_len
        vals.append(val_len)
        vals.append(val)

    elif ttype == SET or ttype == LIST:
        if isinstance(spec, tuple):
            e_type, t_spec = spec[0], spec[1]
        else:
            e_type, t_spec = spec, None

        val_len = len(val)

        fmt += 'bh'
        vals.append(e_type)
        vals.append(val_len)

        for i in range(val_len):
            _fmt, _vals = write_prepare(e_type, val[i], t_spec)
            fmt += _fmt
            vals.extend(_vals)

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

        fmt += 'bbi'
        vals.extend([k_type, v_type, len(val)])

        for k in iter(val):
            v = val[k]
            _fmt, _vals = write_prepare(k_type, k, k_spec)
            fmt += _fmt
            vals.extend(_vals)

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
            fmt += 'bh'
            vals.extend([e_type, i])
            _fmt, _vals = write_prepare(e_type, v, e_container_spec)
            fmt += _fmt
            vals.extend(_vals)
        fmt += 'b'
        vals.extend([STOP])

    return fmt, vals


cpdef bytes write(TType ttype, val, spec=None):
    cdef str fmt
    cdef list vals
    fmt, vals = write_prepare(ttype, val, spec)
    return struct.pack('!' + fmt, *vals)


cpdef bytes write_message_begin(bytes name, TType ttype, int32_t seqid):
    cdef int32_t name_len = len(name)
    cdef str fmt
    fmt = "!ii%dsi" % name_len
    return struct.pack(fmt, VERSION_1 | ttype, name_len, name, seqid)
