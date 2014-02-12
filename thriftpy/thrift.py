"""
    thriftpy.thrift
    ~~~~~~~~~~~~~~~~~~

    Thrift simplified.
"""


class TType(object):
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

    _VALUES_TO_NAMES = {
        STOP: 'STOP',
        VOID: 'VOID',
        BOOL: 'BOOL',
        BYTE: 'BYTE',
        I08: 'BYTE',
        DOUBLE: 'DOUBLE',
        I16: 'I16',
        I32: 'I32',
        I64: 'I64',
        STRING: 'STRING',
        UTF7: 'STRING',
        STRUCT: 'STRUCT',
        MAP: 'MAP',
        SET: 'SET',
        LIST: 'LIST',
        UTF8: 'UTF8',
        UTF16: 'UTF16'
    }


class TMessageType(object):
    CALL = 1
    REPLY = 2
    EXCEPTION = 3
    ONEWAY = 4


class TProcessor(object):
    """Base class for procsessor, which works on two streams."""

    def process(iprot, oprot):
        pass


class TPayload(object):
    thrift_spec = {}

    def read(self, iprot):
        iprot.readStructBegin()

        while True:
            _, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break

            if fid not in self.thrift_spec:
                iprot.skip(ftype)
            else:
                spec = self.thrift_spec[fid]
                spec_type, spec_name, container_spec, _none = spec
                if spec_type == ftype:
                    setattr(self, spec_name,
                            iprot.readFieldByTType(ftype, container_spec))
                else:
                    iprot.skip(ftype)
            iprot.readFieldEnd()

        iprot.readStructEnd()

    def write(self, oprot):
        oprot.writeStructBegin(self.__class__.__name__)

        for fid, spec in self.thrift_spec.items():
            spec_type, spec_name, container_spec, _none = spec
            val = getattr(self, spec_name)
            if val is not None:
                oprot.writeFieldBegin(spec_name, spec_type, fid)
                oprot.writeFieldByTType(spec_type, val, container_spec)
                oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        pass

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class TException(Exception):
    """Base class for all thrift exceptions."""

    @property
    def message(self):
        return str(self)


class TApplicationException(TException, TPayload):
    """Application level thrift exceptions."""

    thrift_spec = {
        1: (TType.STRING, 'message', None, None),
        2: (TType.I32, 'type', None, None),
    }

    UNKNOWN = 0
    UNKNOWN_METHOD = 1
    INVALID_MESSAGE_TYPE = 2
    WRONG_METHOD_NAME = 3
    BAD_SEQUENCE_ID = 4
    MISSING_RESULT = 5
    INTERNAL_ERROR = 6
    PROTOCOL_ERROR = 7

    def __init__(self, message=None, type=UNKNOWN):
        super(TApplicationException, self).__init__(message)
        self.type = type

    def __str__(self):
        if self.message:
            return self.message

        if self.type == self.UNKNOWN_METHOD:
            return 'Unknown method'
        elif self.type == self.INVALID_MESSAGE_TYPE:
            return 'Invalid message type'
        elif self.type == self.WRONG_METHOD_NAME:
            return 'Wrong method name'
        elif self.type == self.BAD_SEQUENCE_ID:
            return 'Bad sequence ID'
        elif self.type == self.MISSING_RESULT:
            return 'Missing result'
        else:
            return 'Default (unknown) TApplicationException'
