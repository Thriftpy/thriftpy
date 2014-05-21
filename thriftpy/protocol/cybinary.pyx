from libc.stdio cimport printf, puts
from libc.stdlib cimport malloc
from libc.string cimport memcpy
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
    size_t int8_sz = sizeof(int8_t)
    size_t int16_sz = sizeof(int16_t)
    size_t int32_sz = sizeof(int32_t)
    size_t int64_sz = sizeof(int64_t)
    size_t double_sz = sizeof(double)

# memprint is a helper to print memory buf in hex code
cdef void memprint(char* buf, size_t sz):
    cdef int i
    for i in range(sz):
        printf("%02x ", <unsigned char> buf[i])
    puts("\n")


##########
# fast pack

cdef void _revert_pack(char* buf, num* x, size_t sz):
    cdef:
        int i
        char* s = <char*> x
    for i in range(sz):
        buf[i] = s[sz-1-i]

cdef void _write_num(char* buf, num val):
    _revert_pack(buf, &val, sizeof(val))

cdef void _write_string(char* buf, bytes val):
    cdef:
        int32_t val_len = len(val)
    _revert_pack(buf, &val_len, int32_sz)
    memcpy(buf + int32_sz, <char*>val, val_len)

cdef bytes _pack_num(num val):
    cdef:
        size_t sz = sizeof(val)
        char* buf = <char*>malloc(sz)
    _revert_pack(buf, &val, sz)
    return buf[:sz]

cdef bytes pack_i8(int8_t val):
    return _pack_num(val)

cdef bytes pack_i16(int16_t val):
    return _pack_num(val)

cdef bytes pack_i32(int32_t val):
    return _pack_num(val)

cdef bytes pack_i64(int64_t val):
    return _pack_num(val)

cdef bytes pack_bool(int8_t bool_):
    if bool_:
        return pack_i8(1)
    else:
        return pack_i8(0)

cdef bytes pack_double(double val):
    return _pack_num(val)

cdef bytes pack_string(bytes val):
    cdef:
        int val_len = len(val)
        size_t sz = sizeof(val_len)
    cdef char* buf = <char*>malloc(sz + val_len)
    _write_string(buf, val)
    return buf[:sz + val_len]


##########
# fast unpack

cdef void _revert_unpack(num* x, char* buf, size_t sz):
    cdef:
        int i
        char tmp

    for i in range(sz / 2):
        tmp = buf[i]
        buf[i] = buf[sz-1-i]
        buf[sz-1-i] = tmp

    memcpy(x, buf, sz)

cdef int8_t unpack_i8(bytes buf):
    cdef:
        char* read = buf
        int8_t x
    memcpy(&x, read, int8_sz)
    return x

cdef int16_t unpack_i16(bytes buf):
    cdef:
        char* read = buf
        int16_t x
    _revert_unpack(&x, read, int16_sz)
    return x

cdef int32_t unpack_i32(bytes buf):
    cdef:
        char* read = buf
        int32_t x
    _revert_unpack(&x, read, int32_sz)
    return x

cdef int64_t unpack_i64(bytes buf):
    cdef:
        char* read = buf
        int64_t x
    _revert_unpack(&x, read, int64_sz)
    return x

cdef double unpack_double(bytes buf):
    cdef:
        char* read = buf
        double x
    _revert_unpack(&x, read, double_sz)
    return x


##########
# thrift binary write

cdef void write_message_begin(outbuf, bytes name, int8_t ttype, int32_t seqid):
    cdef:
        bytes bytes_name = name
        char* buf = <char*>malloc(len(name) + int8_sz + int32_sz * 2)
        int32_t i = VERSION_1 | ttype

    _write_num(buf, i)
    _write_string(buf + int32_sz, bytes_name)
    _write_num(buf + len(name) + int32_sz * 2, seqid)
    outbuf.write(buf[:len(name) + int32_sz * 3])

cdef write_field_begin(outbuf, int8_t ttype, int16_t fid):
    cdef char* buf = <char*>malloc(int8_sz + int16_sz)
    _write_num(buf, ttype)
    _write_num(buf + int8_sz, fid)
    outbuf.write(buf[:int8_sz + int16_sz])

cdef write_field_stop(outbuf):
    outbuf.write(pack_i8(STOP))

cdef write_list_begin(outbuf, int8_t e_type, int32_t size):
    cdef char* buf = <char*>malloc(int8_sz + int32_sz)
    _write_num(buf, e_type)
    _write_num(buf + int8_sz, size)
    outbuf.write(buf[:int8_sz + int32_sz])

cdef write_map_begin(outbuf, int8_t k_type, int8_t v_type, int32_t size):
    cdef char* buf = <char*>malloc(int8_sz * 2 + int32_sz)
    _write_num(buf, k_type)
    _write_num(buf + int8_sz, v_type)
    _write_num(buf + int8_sz * 2, size)
    outbuf.write(buf[:int8_sz * 2 + int32_sz])

cpdef write_val(outbuf, int8_t ttype, val, spec=None):
    cdef:
        int8_t e_type, k_type, v_type, f_type
        int32_t i, val_len, fid
        bytes res = b''
        tuple e_spec
        str f_name

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
        if not isinstance(val, bytes):
            val = val.encode('utf-8')
        outbuf.write(pack_string(val))

    elif ttype == SET or ttype == LIST:
        if isinstance(spec, tuple):
            e_type, t_spec = spec[0], spec[1]
        else:
            e_type, t_spec = spec, None

        val_len = len(val)
        write_list_begin(outbuf, e_type, val_len)
        for i in range(val_len):
            write_val(outbuf, e_type, val[i], t_spec)

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
            write_val(outbuf, k_type, k, k_spec)
            write_val(outbuf, v_type, val[k], v_spec)

    elif ttype == STRUCT:
        for fid in iter(val.thrift_spec):
            f_spec = val.thrift_spec[fid]
            if len(f_spec) == 2:
                f_type, f_name = f_spec
                f_container_spec = None
            else:
                f_type, f_name, f_container_spec = f_spec

            v = getattr(val, f_name)
            if v is None:
                continue

            write_field_begin(outbuf, f_type, fid)
            write_val(outbuf, f_type, v, f_container_spec)
        write_field_stop(outbuf)


##########
# thrift binary read

cdef tuple read_message_begin(inbuf):
    cdef:
        bytes buf, name
        size_t sz
        int32_t seqid

    buf = inbuf.read(8)
    sz = unpack_i32(buf[:4])

    if sz & VERSION_MASK != VERSION_1:
        raise Exception("Bad Version")

    name_sz = unpack_i32(buf[4:])
    name = inbuf.read(name_sz)

    seqid = unpack_i32(inbuf.read(4))
    return name, sz & TYPE_MASK, seqid

cdef tuple read_field_begin(inbuf):
    cdef int8_t ftype = unpack_i8(inbuf.read(1))
    if ftype == STOP:
        return ftype, 0

    return ftype, unpack_i16(inbuf.read(2))

cdef tuple read_list_begin(inbuf):
    cdef bytes buf = inbuf.read(int8_sz + int32_sz)
    return unpack_i8(buf[:1]), unpack_i32(buf[1:])

cdef tuple read_map_begin(inbuf):
    cdef bytes buf = inbuf.read(int8_sz * 2 + int32_sz)
    return unpack_i8(buf[:1]), unpack_i8(buf[1:2]), unpack_i32(buf[2:])

cpdef read_val(inbuf, int8_t ttype, spec=None):
    cdef:
        size_t sz
        int8_t f_type, k_type, v_type, sk_type, sv_type, sf_type
        int32_t i, fid
        str f_name

    if ttype == BOOL:
        return bool(unpack_i8(inbuf.read(int8_sz)))

    elif ttype == BYTE:
        return unpack_i8(inbuf.read(int8_sz))

    elif ttype == I16:
        return unpack_i16(inbuf.read(int16_sz))

    elif ttype == I32:
        return unpack_i32(inbuf.read(int32_sz))

    elif ttype == I64:
        return unpack_i64(inbuf.read(int64_sz))

    elif ttype == DOUBLE:
        return unpack_double(inbuf.read(double_sz))

    elif ttype == STRING:
        sz = unpack_i32(inbuf.read(int32_sz))
        return inbuf.read(sz).decode('utf-8')

    elif ttype == SET or ttype == LIST:
        if isinstance(spec, tuple):
            v_type, v_spec = spec[0], spec[1]
        else:
            v_type, v_spec = spec, None

        result = []
        r_type, sz = read_list_begin(inbuf)
        # the v_type is useless here since we already get it from spec
        if r_type != v_type:
            raise Exception("Message Corrupt")

        for i in range(sz):
            result.append(read_val(inbuf, v_type, v_spec))
        return result

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

        result = {}
        sk_type, sv_type, sz = read_map_begin(inbuf)
        if sk_type != k_type or sv_type != v_type:
            raise Exception("Message Corrupt")

        for i in range(sz):
            k_val = read_val(inbuf, k_type, k_spec)
            v_val = read_val(inbuf, v_type, v_spec)
            result[k_val] = v_val

        return result

    elif ttype == STRUCT:
        # In this case, the spec should be a cls
        obj = spec()
        # The max loop count equals field count + a final stop byte.
        for i in range(len(spec.thrift_spec) + 1):
            f_type, fid = read_field_begin(inbuf)
            if f_type == STOP:
                break

            if fid not in spec.thrift_spec:
                skip(inbuf, f_type)

            if len(spec.thrift_spec[fid]) == 2:
                sf_type, f_name = spec.thrift_spec[fid]
                f_container_spec = None
            else:
                sf_type, f_name, f_container_spec = spec.thrift_spec[fid]

            # it really should equal here. but since we already wasted
            # space storing the duplicate info, let's check it.
            if f_type != sf_type:
                raise Exception("Message Corrupt")

            setattr(obj, f_name,
                    read_val(inbuf, f_type, f_container_spec))
        return obj


##########
# skip field

cdef void skip(inbuf, int8_t ftype) except *:
    cdef:
        int8_t f_type, k_type, v_type
        int32_t sz, fid

    if ftype == BOOL or ftype == BYTE:
        inbuf.read(int8_sz)

    elif ftype == I16:
        inbuf.read(int16_sz)

    elif ftype == I32:
        inbuf.read(int32_sz)

    elif ftype == I64:
        inbuf.read(int64_sz)

    elif ftype == DOUBLE:
        inbuf.read(double_sz)

    elif ftype == STRING:
        inbuf.read(unpack_i32(inbuf.read(int32_sz)))

    elif ftype == SET or LIST:
        v_type, sz = read_list_begin(inbuf)
        for i in range(sz):
            skip(inbuf, v_type)

    elif ftype == MAP:
        k_type, v_type, sz = read_map_begin(inbuf)
        for i in range(sz):
            skip(inbuf, k_type)
            skip(inbuf, v_type)

    elif ftype == STRUCT:
        while True:
            f_type, fid = read_field_begin(inbuf)
            if f_type == STOP:
                break
            skip(inbuf, f_type)


cdef class TCyBinaryProtocol:
    cdef public object trans

    def __init__(self, object trans):
        self.trans = trans

    def __cinit__(self, object trans):
        self.trans = trans

    cpdef read_message_begin(self):
        api, ttype, seqid = read_message_begin(self.trans)
        return api.decode('utf-8'), ttype, seqid

    cpdef read_message_end(self):
        pass

    cpdef write_message_begin(self, name, ttype, seqid):
        write_message_begin(self.trans, name.encode('utf-8'), ttype, seqid)

    cpdef write_message_end(self):
        pass

    cpdef read_struct(self, obj_cls):
        return read_val(self.trans, STRUCT, obj_cls)

    cpdef write_struct(self, obj):
        write_val(self.trans, STRUCT, obj)


cdef class TCyBinaryProtocolFactory:
    cpdef TCyBinaryProtocol get_protocol(self, object trans):
        return TCyBinaryProtocol.__new__(TCyBinaryProtocol, trans)
