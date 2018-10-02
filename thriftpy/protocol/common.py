from ..thrift import BINARY


def process_read_string_or_binary(byte_payload, spec, decode_response):
    # This condition is constructed so that any non-auto true-ish
    # decode_response value will be considered true (better safe than sorry)
    if (
        decode_response == 'auto' and spec != BINARY or
        decode_response != 'auto' and decode_response
    ):
        try:
            return byte_payload.decode('utf-8')
        except UnicodeDecodeError:
            if decode_response == 'auto':
                raise
    return byte_payload
