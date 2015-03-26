from thriftpy.thrift import TMultiplexingProcessor


class TMultiplexingProtocol(object):

    """

    Multiplex protocol

    for writing message begin, it prepend the service name to the api
    for other functions, it simply delegate to the original protocol

    """

    def __init__(self, proto, service_name):
        self.service_name = service_name
        self.proto = proto

    def __getattr__(self, name):
        return getattr(self.proto, name)

    def write_message_begin(self, name, ttype, seqid):
        self.proto.write_message_begin(
            self.service_name + TMultiplexingProcessor.Separator + name,
            ttype, seqid)

class TMultiplexingProtocolFactory(object):

    def __init__(self, proto_factory, service_name):
        self.proto_factory = proto_factory
        self.service_name = service_name

    def get_protocol(self, trans):
        proto = self.proto_factory.get_protocol(trans)
        multi_proto = TMultiplexingProtocol(proto, self.service_name)
        return multi_proto
