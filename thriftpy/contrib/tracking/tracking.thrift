/*
 * Used to store call info.
 */
struct RequestInfo {
    1: string request_id // used to identify a request
    2: string api // api name
    3: string seq // sequence number
    4: string client // client name
    5: string server // server name
    6: bool status // request status
    7: i64 start // start timestamp
    8: i64 end // end timestamp
}

/*
 * This is the structure used to send call info to server.
 */
struct RequestHeader {
    1: string request_id
    2: string seq
}

/**
 * This is the struct that a successful upgrade will reply with.
 */
struct UpgradeReply {}
struct UpgradeArgs {}
