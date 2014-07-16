from libc.stdlib cimport malloc, free


class ProtocolError(Exception):
    pass


cdef class TCyBinaryProtocol(object):
    DEF DEFAULT_BUFFER = 4096
    DEF VERSION_MASK = -65536
    DEF VERSION_1 = -2147418112
    DEF TYPE_MASK = 0x000000ff
    DEF FIELD_STOP = 0

    cdef BinaryRW buf
    cdef public object trans

    def __init__(self, trans, int buf_size=DEFAULT_BUFFER):
        self.trans = trans
        self.buf = BinaryRW(trans, buf_size)

    def read_message_begin(self):
        cdef int32_t mgk, version, msg_type, seq_id
        self.buf.read_int32(&mgk)
        version = mgk & VERSION_MASK
        if version != VERSION_1:
            raise ProtocolError('invalid version %d' % version)
        msg_type = mgk & TYPE_MASK

        name = self.buf.read_string()
        self.buf.read_int32(&seq_id)
        return name, msg_type, seq_id

    def read_message_end(self):
        pass

    def write_message_begin(self, name, int msg_type, int32_t seq_id):
        cdef uint32_t mgk = VERSION_1 | msg_type
        self.buf.write_int32(mgk)
        self.buf.write_string(name)
        self.buf.write_int32(seq_id)

    def write_message_end(self):
        self.buf.write_flush()

    def read_struct(self, obj):
        cdef dict field_specs = obj.thrift_spec
        cdef int total_argn = len(field_specs)
        cdef byte field_type, field_type_defed
        cdef int16_t field_id

        for i in range(total_argn + 1):
            self.buf.read_byte(&field_type)
            if field_type == FIELD_STOP:
                break
            self.buf.read_int16(&field_id)
            field_spec = field_specs.get(field_id, None)
            if field_spec is None:
                self.skip_val(field_type)
            else:
                if len(field_spec) == 2:
                    field_type_defed, field_name = field_spec
                    container_spec = None
                else:
                    field_type_defed, field_name, container_spec = field_spec
                if field_type != field_type_defed:
                    raise ProtocolError(
                        'field type mismatch: got %d, expected %d' % (
                        field_type, field_type_defed))
                val = self.read_val(field_type, container_spec)
                setattr(obj, field_name, val)
        return obj

    def write_struct(self, obj):
        for field_id, field_spec in obj.thrift_spec.items():
            if len(field_spec) == 2:
                f_type, f_name = field_spec
                f_container_spec = None
            else:
                f_type, f_name, f_container_spec = field_spec
            self.buf.write_byte(f_type)
            self.buf.write_int16(field_id)
            self.write_val(f_type, getattr(obj, f_name), f_container_spec)
        self.buf.write_byte(FIELD_STOP)

    def read_val(self, byte field_type, spec=None):
        cdef byte byte_v, k_type, v_type
        cdef int16_t int16_v
        cdef int32_t int32_v
        cdef int64_t int64_v
        cdef double double_v

        if field_type == T_TYPE_I32:
            self.buf.read_int32(&int32_v)
            return int32_v
        elif field_type == T_TYPE_STRING or field_type == T_TYPE_UTF8:
            return self.buf.read_string()
        elif field_type == T_TYPE_I64:
            self.buf.read_int64(&int64_v)
            return int64_v
        elif field_type == T_TYPE_I16:
            self.buf.read_int16(&int16_v)
            return int16_v
        elif field_type == T_TYPE_DOUBLE:
            self.buf.read_double(&double_v)
            return double_v
        elif field_type == T_TYPE_BOOL:
            self.buf.read_byte(&byte_v)
            return byte_v == 1
        elif field_type == T_TYPE_STRUCT:
            return self.read_struct(spec())
        elif field_type == T_TYPE_MAP:
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
            self.buf.read_byte(&byte_v)
            if byte_v != k_type:
                raise ProtocolError(
                    'map key type mismatch: got %d, expected %d' % (
                        byte_v, k_type))
            self.buf.read_byte(&byte_v)
            if byte_v != v_type:
                raise ProtocolError(
                    'map value type mismatch: got %d, expected %d' % (
                        byte_v, v_type))
            self.buf.read_int32(&int32_v)
            return {self.read_val(k_type, k_spec): self.read_val(v_type, v_spec)
                for i in range(int32_v)}
        elif field_type == T_TYPE_LIST or field_type == T_TYPE_SET:
            if isinstance(spec, tuple):
                item_type, item_spec = spec[0], spec[1]
            else:
                item_type, item_spec = spec, None
            self.buf.read_byte(&byte_v)
            self.buf.read_int32(&int32_v)
            if byte_v != item_type:
                raise ProtocolError(
                    'list/set item type mismatch: got %d, expected %d' % (
                        item_type, byte_v))
            return [self.read_val(byte_v, item_spec)
                    for i in range(int32_v)]
        elif field_type == T_TYPE_BYTE or field_type == T_TYPE_I08:
            self.buf.read_byte(&byte_v)
            return byte_v
        else:
            raise ProtocolError('unsupportted field type: %d' % field_type)

    def write_val(self, field_type, obj, spec=None):
        if field_type == T_TYPE_I32:
            self.buf.write_int32(obj)
        elif field_type == T_TYPE_STRING or field_type == T_TYPE_UTF8:
            self.buf.write_string(obj)
        elif field_type == T_TYPE_I64:
            self.buf.write_int64(obj)
        elif field_type == T_TYPE_I16:
            self.buf.write_int16(obj)
        elif field_type == T_TYPE_DOUBLE:
            self.buf.write_double(obj)
        elif field_type == T_TYPE_BOOL:
            self.buf.write_byte(obj)
        elif field_type == T_TYPE_STRUCT:
            self.write_struct(obj)
        elif field_type == T_TYPE_MAP:
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
            self.buf.write_byte(k_type)
            self.buf.write_byte(v_type)
            self.buf.write_int32(len(obj))
            for k, v in obj.items():
                self.write_val(k_type, k, k_spec)
                self.write_val(v_type, v, v_spec)
        elif field_type == T_TYPE_LIST or field_type == T_TYPE_SET:
            if isinstance(spec, tuple):
                item_type, item_spec = spec[0], spec[1]
            else:
                item_type, item_spec = spec, None
            self.buf.write_byte(item_type)
            self.buf.write_int32(len(obj))
            for item in obj:
                self.write_val(item_type, item, item_spec)
        elif field_type == T_TYPE_BYTE or field_type == T_TYPE_I08:
            self.buf.write_byte(obj)
        else:
            raise ProtocolError('unsupportted field type: %d' % field_type)

    cdef skip_val(self, byte field_type):
        raise ProtocolError('skip')


class TCyBinaryProtocolFactory(object):
    def get_protocol(self, trans):
        return TCyBinaryProtocol(trans)
