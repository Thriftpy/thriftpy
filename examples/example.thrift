const i16 DEFAULT = 10
const i16 MAX = 200

enum MessageStatus {
    VALID = 0,
    INVALID = 1,
}

struct Item {
    1: optional i32 id,
    2: optional string name,
}

service ExampleService {
    bool ping();
    string hello(1: string name);
}
