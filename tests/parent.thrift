include "base.thrift"

struct Greet {
    1: optional base.Hello hello,
    2: optional base.timestamp date,
    3: optional base.Code code
}
