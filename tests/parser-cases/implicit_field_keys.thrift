exception NetworkError {
    string message,
    i32 http_code,
}

service Service {
    bool send(i64 id, string message)
        throws (NetworkError network_error)
}
