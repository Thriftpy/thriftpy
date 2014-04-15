import struct

from .thrift import TType, TException


class TProtocolException(TException):
    """Custom Protocol Exception class"""

    UNKNOWN = 0
    INVALID_DATA = 1
    NEGATIVE_SIZE = 2
    SIZE_LIMIT = 3
    BAD_VERSION = 4

    def __init__(self, type=UNKNOWN, message=None):
        TException.__init__(self, message)
        self.type = type


cdef class TBinaryProtocol:
    """Binary implementation of the Thrift protocol driver."""

    cdef int VERSION_1, VERSION_MASK, TYPE_MASK
    cdef public object trans

    def __init__(self, object trans):
        self.trans = trans

        # VERSION_MASK = -65536
        self.VERSION_MASK = 0xffff0000
        # VERSION_1 = -2147418112
        self.VERSION_1 = 0x80010000
        self.TYPE_MASK = 0x000000ff

    def __cinit__(self, object trans):
        self.trans = trans

        # VERSION_MASK = -65536
        self.VERSION_MASK = 0xffff0000
        # VERSION_1 = -2147418112
        self.VERSION_1 = 0x80010000
        self.TYPE_MASK = 0x000000ff


    cdef tuple _parse_spec(self, tuple spec):
        return spec + (None,) if len(spec) == 2 else spec

    cpdef writeMessageBegin(self, str name, signed char type_, int seqid):
        self.writeI32(self.VERSION_1 | type_)
        self.writeString(name.encode('utf-8'))
        self.writeI32(seqid)

    cpdef writeMessageEnd(self):
        pass

    cdef void writeStructBegin(self, str name):
        pass

    cdef writeStructEnd(self):
        pass

    cdef void writeFieldBegin(self, str name, signed char type_, int id_):
        self.writeByte(type_)
        self.writeI16(id_)

    cdef void writeFieldEnd(self):
        pass

    cdef void writeFieldStop(self):
        self.writeByte(TType.STOP)

    cdef void writeMapBegin(self, signed char ktype, signed char vtype, int size):
        self.writeByte(ktype)
        self.writeByte(vtype)
        self.writeI32(size)

    cdef void writeMapEnd(self):
        pass

    cdef void writeListBegin(self, signed char etype, int size):
        self.writeByte(etype)
        self.writeI32(size)

    cdef void writeListEnd(self):
        pass

    cdef void writeSetBegin(self, signed char etype, int size):
        self.writeListBegin(etype, size)

    cdef void writeSetEnd(self):
        self.writeListEnd()

    cdef writeBool(self, signed char bool_):
        if bool_:
            self.writeByte(1)
        else:
            self.writeByte(0)

    cdef void writeByte(self, signed char byte):
        buff = struct.pack("!b", byte)
        self.trans.write(buff)

    cdef void writeI16(self, short i16):
        buff = struct.pack("!h", i16)
        self.trans.write(buff)

    cdef void writeI32(self, int i32):
        buff = struct.pack("!i", i32)
        self.trans.write(buff)

    cdef void writeI64(self, long long i64):
        buff = struct.pack("!q", i64)
        self.trans.write(buff)

    cdef void writeDouble(self, double d):
        buff = struct.pack("!d", d)
        self.trans.write(buff)

    cdef void writeString(self, bytes string):
        self.writeI32(len(string))
        self.trans.write(string)

    cpdef tuple readMessageBegin(self):
        sz = self.readI32()
        version = sz & self.VERSION_MASK
        if version != self.VERSION_1:
            raise TProtocolException(
                type=TProtocolException.BAD_VERSION,
                message='Bad version in readMessageBegin: %d' % (sz))
        type_ = sz & self.TYPE_MASK
        name = self.readString()
        seqid = self.readI32()
        return name, type_, seqid

    cpdef readMessageEnd(self):
        pass

    cdef void readStructBegin(self):
        pass

    cdef void readStructEnd(self):
        pass

    cdef tuple readFieldBegin(self):
        type_ = self.readByte()
        if type_ == TType.STOP:
            return None, type_, 0
        id = self.readI16()
        return None, type_, id

    cdef void readFieldEnd(self):
        pass

    cdef tuple readMapBegin(self):
        ktype = self.readByte()
        vtype = self.readByte()
        size = self.readI32()
        return ktype, vtype, size

    cdef void readMapEnd(self):
        pass

    cdef tuple readListBegin(self):
        etype = self.readByte()
        size = self.readI32()
        return etype, size

    cdef void readListEnd(self):
        pass

    cdef tuple readSetBegin(self):
        return self.readListBegin()

    cdef void readSetEnd(self):
        self.readListEnd()

    cdef signed char readBool(self):
        byte = self.readByte()
        return byte != 0

    cdef signed char readByte(self):
        buff = self.trans.readAll(1)
        val, = struct.unpack('!b', buff)
        return val

    cdef short readI16(self):
        buff = self.trans.readAll(2)
        val, = struct.unpack('!h', buff)
        return val

    cdef int readI32(self):
        buff = self.trans.readAll(4)
        val, = struct.unpack('!i', buff)
        return val

    cdef long long readI64(self):
        buff = self.trans.readAll(8)
        val, = struct.unpack('!q', buff)
        return val

    cdef double readDouble(self):
        buff = self.trans.readAll(8)
        val, = struct.unpack('!d', buff)
        return val

    cdef str readString(self):
        length = self.readI32()
        return self.trans.readAll(length).decode('utf-8')

    cdef void skip(self, signed char _type):
        if _type == TType.STOP:
            return
        elif _type == TType.BOOL:
            self.readBool()
        elif _type == TType.BYTE:
            self.readByte()
        elif _type == TType.I16:
            self.readI16()
        elif _type == TType.I32:
            self.readI32()
        elif _type == TType.I64:
            self.readI64()
        elif _type == TType.DOUBLE:
            self.readDouble()
        elif _type == TType.STRING:
            self.readString()
        elif _type == TType.STRUCT:
            self.readStructBegin()
            while True:
                name, _type, _id = self.readFieldBegin()
                if _type == TType.STOP:
                    break
                self.skip(_type)
                self.readFieldEnd()
            self.readStructEnd()
        elif _type == TType.MAP:
            ktype, vtype, size = self.readMapBegin()
            for i in range(size):
                self.skip(ktype)
                self.skip(vtype)
            self.readMapEnd()
        elif _type == TType.SET:
            etype, size = self.readSetBegin()
            for i in range(size):
                self.skip(etype)
            self.readSetEnd()
        elif _type == TType.LIST:
            etype, size = self.readListBegin()
            for i in range(size):
                self.skip(etype)
            self.readListEnd()

    cdef readFieldByTType(self, signed char ttype, spec):
        if ttype == 2:
            return self.readBool()
        elif ttype == 3:
            return self.readByte()
        elif ttype == 4:
            return self.readDouble()
        elif ttype == 6:
            return self.readI16()
        elif ttype == 8:
            return self.readI32()
        elif ttype == 10:
            return self.readI64()
        elif ttype == 11:
            return self.readString()
        elif ttype == 12:
            return self.readContainerStruct(spec)
        elif ttype == 13:
            return self.readContainerMap(spec)
        elif ttype == 14:
            return self.readContainerSet(spec)
        elif ttype == 15:
            return self.readContainerList(spec)
        else:
            raise TProtocolException(type=TProtocolException.INVALID_DATA,
                                     message='Invalid field type %d' % (ttype))

    cdef readContainerList(self, spec):
        if isinstance(spec, int):
            ttype, tspec = spec, None
        else:
            ttype, tspec = spec[0], spec[1]

        results = []
        list_type, list_len = self.readListBegin()
        cdef int e
        if tspec is None:
            for e in range(list_len):
                results.append(self.readFieldByTType(ttype, tspec))
        else:
            for e in range(list_len):
                results.append(self.readFieldByTType(list_type, tspec))
        self.readListEnd()
        return results

    cdef readContainerSet(self, tuple spec):
        return set(self.readContainerList(spec))

    cdef readContainerStruct(self, obj_class):
        obj = obj_class()
        obj.read(self)
        return obj

    cdef readContainerMap(self, tuple spec):
        results = dict()
        key_ttype, val_ttype = spec
        map_ktype, map_vtype, map_len = self.readMapBegin()
        if isinstance(key_ttype, int):
            key_spec = None
        else:
            key_ttype, key_spec = key_ttype
        if isinstance(val_ttype, int):
            val_spec = None
        else:
            val_ttype, val_spec = val_ttype

        cdef int i
        for i in range(map_len):
            k_val = self.readFieldByTType(key_ttype, key_spec)
            v_val = self.readFieldByTType(val_ttype, val_spec)
            results[k_val] = v_val
        self.readMapEnd()
        return results

    cpdef readStruct(self, obj, thrift_spec):
        self.readStructBegin()
        while True:
            _, ftype, fid = self.readFieldBegin()
            if ftype == TType.STOP:
                break

            if fid not in thrift_spec:
                self.skip(ftype)
            else:
                spec = thrift_spec[fid]
                spec_type, spec_name, container_spec = self._parse_spec(spec)
                if spec_type == ftype:
                    setattr(obj, spec_name,
                            self.readFieldByTType(ftype, container_spec))
                else:
                    self.skip(ftype)
            self.readFieldEnd()
        self.readStructEnd()

    cdef writeContainerStruct(self, val, spec):
        val.write(self)

    cdef void writeContainerList(self, val, spec):
        if isinstance(spec, int):
            ttype, tspec = spec, None
        else:
            ttype, tspec = spec[0], spec[1]

        self.writeListBegin(ttype, len(val))
        for e in val:
            self.writeFieldByTType(ttype, e, tspec)
        self.writeListEnd()

    cdef void writeContainerSet(self, val, spec):
        self.writeContainerList(val, spec)

    cdef void writeContainerMap(self, val, spec):
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

        self.writeMapBegin(k_type, v_type, len(val))
        for m_key, m_val in val.items():
            self.writeFieldByTType(k_type, m_key, k_spec)
            self.writeFieldByTType(v_type, m_val, v_spec)
        self.writeMapEnd()

    cpdef writeStruct(self, obj, thrift_spec):
        self.writeStructBegin(obj.__class__.__name__)
        # for field in thrift_spec:
        for fid, spec in thrift_spec.items():
            spec_type, spec_name, container_spec = self._parse_spec(spec)
            val = getattr(obj, spec_name)
            if val is None:
                continue
            # get the writer method for this value
            self.writeFieldBegin(spec_name, spec_type, fid)
            self.writeFieldByTType(spec_type, val, container_spec)
            self.writeFieldEnd()
        self.writeFieldStop()
        self.writeStructEnd()

    cdef void writeFieldByTType(self, signed char ttype, val, spec):
        if ttype == 2:
            self.writeBool(val)
        elif ttype == 3:
            self.writeByte(val)
        elif ttype == 4:
            self.writeDouble(val)
        elif ttype == 6:
            self.writeI16(val)
        elif ttype == 8:
            self.writeI32(val)
        elif ttype == 10:
            self.writeI64(val)
        elif ttype == 11:
            self.writeString(val.encode("utf-8"))
        elif ttype == 12:
            self.writeContainerStruct(val, spec)
        elif ttype == 13:
            self.writeContainerMap(val, spec)
        elif ttype == 14:
            self.writeContainerSet(val, spec)
        elif ttype == 15:
            self.writeContainerList(val, spec)
        else:
            raise TProtocolException(type=TProtocolException.INVALID_DATA,
                                     message='Invalid field type %d' % (ttype))



cdef class TBinaryProtocolFactory:
    cdef public TBinaryProtocol trans

    cpdef getProtocol(self, object trans):
        return TBinaryProtocol.__new__(TBinaryProtocol, trans)
