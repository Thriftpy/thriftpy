include "structs.thrift"
include "enums.thrift"

struct Both {
  1: structs.Person person;
  2: enums.Enum1 enum1;
}
