exception NetError {}

service SMS extends BasicService {
    string get_message_by_id(1: required i32 id),
    oneway void send(1: required string to) throws (
        1: NetError net_error
    )
}
