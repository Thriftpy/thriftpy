
DEF T_TYPE_STOP = 0
DEF T_TYPE_VOID = 1
DEF T_TYPE_BOOL = 2
DEF T_TYPE_BYTE = 3
DEF T_TYPE_I08 = 3
DEF T_TYPE_DOUBLE = 4
DEF T_TYPE_I16 = 6
DEF T_TYPE_I32 = 8
DEF T_TYPE_I64 = 10
DEF T_TYPE_STRING = 11
DEF T_TYPE_UTF7 = 11
DEF T_TYPE_BINARY = 11
DEF T_TYPE_STRUCT = 12
DEF T_TYPE_MAP = 13
DEF T_TYPE_SET = 14
DEF T_TYPE_LIST = 15
DEF T_TYPE_UTF8 = 16
DEF T_TYPE_UTF16 = 17

DEF VERSION_1 = -2147352576
DEF DEFAULT_BUFFER = 4096
DEF VERSION_MASK = -65536
DEF TYPE_MASK = 0x000000ff
DEF FIELD_STOP = 0

DEF OLDER_COMPATIBLE_VERSION = (-2147418112,)

cdef public enum exports:
    CURRENT_VERSION = VERSION_1

ctypedef unsigned char byte

from libc.stdint cimport *

cdef extern from 'endian_port.h':
    int16_t htobe16(int16_t n)
    int32_t htobe32(int32_t n)
    int64_t htobe64(int64_t n)
    int16_t be16toh(int16_t n)
    int32_t be32toh(int32_t n)
    int64_t be64toh(int64_t n)
