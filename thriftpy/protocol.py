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


class TBinaryProtocol(object):
    """Binary implementation of the Thrift protocol driver."""

    # NastyHaxx. Python 2.4+ on 32-bit machines forces hex constants to be
    # positive, converting this into a long. If we hardcode the int value
    # instead it'll stay in 32 bit-land.

    # VERSION_MASK = 0xffff0000
    VERSION_MASK = -65536
    # VERSION_1 = 0x80010000
    VERSION_1 = -2147418112
    TYPE_MASK = 0x000000ff

    # tuple of: ('reader method' name, 'writer_method' name, is_container bool)
    _TTYPE_HANDLERS = [
        (None, None, False),    # 0 TType.STOP
        (None, None, False),    # 1 TType.VOID # TODO: handle void?
        ('readBool', 'writeBool', False),    # 2 TType.BOOL
        ('readByte', 'writeByte', False),    # 3 TType.BYTE and I08
        ('readDouble', 'writeDouble', False),    # 4 TType.DOUBLE
        (None, None, False),    # 5 undefined
        ('readI16', 'writeI16', False),    # 6 TType.I16
        (None, None, False),    # 7 undefined
        ('readI32', 'writeI32', False),    # 8 TType.I32
        (None, None, False),    # 9 undefined
        ('readI64', 'writeI64', False),    # 10 TType.I64
        ('readString', 'writeString', False),    # 11 TType.STRING and UTF7
        ('readContainerStruct', 'writeContainerStruct', True),    # 12 *.STRUCT
        ('readContainerMap', 'writeContainerMap', True),    # 13 TType.MAP
        ('readContainerSet', 'writeContainerSet', True),    # 14 TType.SET
        ('readContainerList', 'writeContainerList', True),    # 15 TType.LIST
        (None, None, False),    # 16 TType.UTF8 # TODO: handle utf8 types?
        (None, None, False)    # 17 TType.UTF16 # TODO: handle utf16 types?
    ]

    def __init__(self, trans):
        self.trans = trans

    def writeMessageBegin(self, name, type_, seqid):
        self.writeI32(TBinaryProtocol.VERSION_1 | type_)
        self.writeString(name)
        self.writeI32(seqid)

    def writeMessageEnd(self):
        pass

    def writeStructBegin(self, name):
        pass

    def writeStructEnd(self):
        pass

    def writeFieldBegin(self, name, type, id):
        self.writeByte(type)
        self.writeI16(id)

    def writeFieldEnd(self):
        pass

    def writeFieldStop(self):
        self.writeByte(TType.STOP)

    def writeMapBegin(self, ktype, vtype, size):
        self.writeByte(ktype)
        self.writeByte(vtype)
        self.writeI32(size)

    def writeMapEnd(self):
        pass

    def writeListBegin(self, etype, size):
        self.writeByte(etype)
        self.writeI32(size)

    def writeListEnd(self):
        pass

    def writeSetBegin(self, etype, size):
        return self.writeListBegin(etype, size)

    def writeSetEnd(self):
        return self.writeListEnd()

    def writeBool(self, bool_):
        self.writeByte(1) if bool_ else self.writeByte(0)

    def writeByte(self, byte):
        buff = struct.pack("!b", byte)
        self.trans.write(buff)

    def writeI16(self, i16):
        buff = struct.pack("!h", i16)
        self.trans.write(buff)

    def writeI32(self, i32):
        buff = struct.pack("!i", i32)
        self.trans.write(buff)

    def writeI64(self, i64):
        buff = struct.pack("!q", i64)
        self.trans.write(buff)

    def writeDouble(self, dub):
        buff = struct.pack("!d", dub)
        self.trans.write(buff)

    def writeString(self, string):
        self.writeI32(len(string))
        self.trans.write(string.encode("utf-8"))

    def readMessageBegin(self):
        sz = self.readI32()
        version = sz & TBinaryProtocol.VERSION_MASK
        if version != TBinaryProtocol.VERSION_1:
            raise TProtocolException(
                type=TProtocolException.BAD_VERSION,
                message='Bad version in readMessageBegin: %d' % (sz))
        type_ = sz & TBinaryProtocol.TYPE_MASK
        name = self.readString()
        seqid = self.readI32()
        return name, type_, seqid

    def readMessageEnd(self):
        pass

    def readStructBegin(self):
        pass

    def readStructEnd(self):
        pass

    def readFieldBegin(self):
        type_ = self.readByte()
        if type_ == TType.STOP:
            return None, type_, 0
        id = self.readI16()
        return None, type_, id

    def readFieldEnd(self):
        pass

    def readMapBegin(self):
        ktype = self.readByte()
        vtype = self.readByte()
        size = self.readI32()
        return ktype, vtype, size

    def readMapEnd(self):
        pass

    def readListBegin(self):
        etype = self.readByte()
        size = self.readI32()
        return etype, size

    def readListEnd(self):
        pass

    def readSetBegin(self):
        return self.readListBegin()

    def readSetEnd(self):
        return self.readListEnd()

    def readBool(self):
        byte = self.readByte()
        return byte != 0

    def readByte(self):
        buff = self.trans.readAll(1)
        val, = struct.unpack('!b', buff)
        return val

    def readI16(self):
        buff = self.trans.readAll(2)
        val, = struct.unpack('!h', buff)
        return val

    def readI32(self):
        buff = self.trans.readAll(4)
        val, = struct.unpack('!i', buff)
        return val

    def readI64(self):
        buff = self.trans.readAll(8)
        val, = struct.unpack('!q', buff)
        return val

    def readDouble(self):
        buff = self.trans.readAll(8)
        val, = struct.unpack('!d', buff)
        return val

    def readString(self):
        length = self.readI32()
        string = self.trans.readAll(length)
        return string.decode('utf-8')

    def skip(self, _type):
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
            name = self.readStructBegin()
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

    def readFieldByTType(self, ttype, spec):
        try:
            r_handler = self._TTYPE_HANDLERS[ttype][0]
        except IndexError:
            raise TProtocolException(type=TProtocolException.INVALID_DATA,
                                     message='Invalid field type %d' % (ttype))
        if r_handler is None:
            raise TProtocolException(type=TProtocolException.INVALID_DATA,
                                     message='Invalid field type %d' % (ttype))
        reader = getattr(self, r_handler)
        if spec is None:
            return reader()
        return reader(spec)

    def readContainerList(self, spec):
        if isinstance(spec, int):
            ttype, tspec = spec, None
        else:
            ttype, tspec = spec[0], spec[1]

        r_handler = self._TTYPE_HANDLERS[ttype][0]
        reader = getattr(self, r_handler)
        list_type, list_len = self.readListBegin()

        results = []
        if tspec is None:
            # list values are simple types
            for idx in range(list_len):
                results.append(reader())
        else:
            # this is like an inlined readFieldByTType
            container_reader = self._TTYPE_HANDLERS[list_type][0]
            val_reader = getattr(self, container_reader)
            for idx in range(list_len):
                results.append(val_reader(tspec))
        self.readListEnd()
        return results

    def readContainerSet(self, spec):
        return set(self.readContainerList(spec))

    def readContainerStruct(self, obj_class):
        obj = obj_class()
        obj.read(self)
        return obj

    def readContainerMap(self, spec):
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

        # TODO: compare types we just decoded with thrift_spec and
        # abort/skip if types disagree
        key_reader = getattr(self, self._TTYPE_HANDLERS[key_ttype][0])
        val_reader = getattr(self, self._TTYPE_HANDLERS[val_ttype][0])

        # list values are simple types
        for idx in range(map_len):
            if key_spec is None:
                k_val = key_reader()
            else:
                k_val = self.readFieldByTType(key_ttype, key_spec)
            if val_spec is None:
                v_val = val_reader()
            else:
                v_val = self.readFieldByTType(val_ttype, val_spec)
            # this raises a TypeError with unhashable keys types
            # i.e. this fails: d=dict(); d[[0,1]] = 2
            results[k_val] = v_val
        self.readMapEnd()
        return results

    def readStruct(self, obj, thrift_spec):
        self.readStructBegin()
        while True:
            fname, ftype, fid = self.readFieldBegin()
            if ftype == TType.STOP:
                break
            try:
                field = thrift_spec[fid]
            except IndexError:
                self.skip(ftype)
            else:
                if field is not None and ftype == field[1]:
                    fname = field[2]
                    fspec = field[3]
                    val = self.readFieldByTType(ftype, fspec)
                    setattr(obj, fname, val)
                else:
                    self.skip(ftype)
            self.readFieldEnd()
        self.readStructEnd()

    def writeContainerStruct(self, val, spec):
        val.write(self)

    def writeContainerList(self, val, spec):
        self.writeListBegin(spec[0], len(val))
        r_handler, w_handler, is_container = self._TTYPE_HANDLERS[spec[0]]
        e_writer = getattr(self, w_handler)
        if not is_container:
            for elem in val:
                e_writer(elem)
        else:
            for elem in val:
                e_writer(elem, spec[1])
        self.writeListEnd()

    def writeContainerSet(self, val, spec):
        return self.writeContainerList(val, spec)

    def writeContainerMap(self, val, spec):
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

        ktype_name = self._TTYPE_HANDLERS[k_type][1]
        vtype_name = self._TTYPE_HANDLERS[v_type][1]
        k_writer = getattr(self, ktype_name)
        v_writer = getattr(self, vtype_name)

        self.writeMapBegin(k_type, v_type, len(val))
        for m_key, m_val in val.items():
            if k_spec is None:
                k_writer(m_key)
            else:
                k_writer(m_key, k_spec)
            if v_spec is None:
                v_writer(m_val)
            else:
                v_writer(m_val, v_spec)
        self.writeMapEnd()

    def writeStruct(self, obj, thrift_spec):
        self.writeStructBegin(obj.__class__.__name__)
        # for field in thrift_spec:
        for fid, spec in thrift_spec.items():
            spec_type, spec_name, container_spec, _none = spec
            val = getattr(obj, spec_name)
            if val is None:
                continue
            # get the writer method for this value
            self.writeFieldBegin(spec_name, spec_type, fid)
            self.writeFieldByTType(spec_type, val, container_spec)
            self.writeFieldEnd()
        self.writeFieldStop()
        self.writeStructEnd()

    def writeFieldByTType(self, ttype, val, spec):
        r_handler, w_handler, is_container = self._TTYPE_HANDLERS[ttype]
        writer = getattr(self, w_handler)
        if is_container:
            writer(val, spec)
        else:
            writer(val)


class TBinaryProtocolFactory(object):
    def getProtocol(self, trans):
        return TBinaryProtocol(trans)
