struct Item {
    1: optional i32 id,
    2: optional string name,
}

service ExampleService {
    bool ping();
    string hello(1: string name);
    Item make(1: i32 id, 2: string name);
}
