include "structs.thrift"
include "enums.thrift"
include "typedefs.thrift"

struct Both {
  1: structs.Person person;
  2: enums.Enum1 enum1;
  3: typedefs.bytes bytes;
}
