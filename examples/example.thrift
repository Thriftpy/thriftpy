const i16 DEFAULT = 10
const i16 MAX = 200

enum MessageStatus {
    VALID = 0,
    INVALID = 1,
}

struct TItem {
    1: required i32 id,
    2: optional string item_name,
}

service ExampleService {
    bool ping();
    string hello(1: string name);
    TItem make(1: i32 id, 2: string name);
}
