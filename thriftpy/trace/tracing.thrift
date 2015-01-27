/**
 * This is the structure used to send call info to server.
 */
struct RequestHeader {
    1: string request_id // used to identify a request
    2: i32 seq // sequence number
    3: string client // client name
    4: string server // server name
    5: bool status // request status
    6: i64 start // start timestamp
    7: i64 end // end timestamp
}

/**
 * This is the struct that a successful upgrade will reply with.
 */
struct UpgradeReply {}

struct UpgradeArgs {}
