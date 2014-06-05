import time

from thrift.TSerialization import serialize, deserialize
from thrift.protocol.TBinaryProtocol import (
    TBinaryProtocolFactory,
    TBinaryProtocolAcceleratedFactory
)

from addressbook import ttypes


def make_addressbook():
    phone1 = ttypes.PhoneNumber()
    phone1.type = ttypes.PhoneType.MOBILE
    phone1.number = b'555-1212'
    phone2 = ttypes.PhoneNumber()
    phone2.type = ttypes.PhoneType.HOME
    phone2.number = b'555-1234'
    person = ttypes.Person()
    person.name = b"Alice"
    person.phones = [phone1, phone2]
    person.created_at = 1400000000

    ab = ttypes.AddressBook()
    ab.people = {person.name: person}
    return ab


def encode(n, proto_factory=TBinaryProtocolFactory()):
    ab = make_addressbook()
    start = time.time()
    for i in range(n):
        serialize(ab, proto_factory)
    end = time.time()
    print("encode\t-> {}".format(end - start))


def decode(n, proto_factory=TBinaryProtocolFactory()):
    ab = ttypes.AddressBook()
    ab_encoded = serialize(make_addressbook())
    start = time.time()
    for i in range(n):
        deserialize(ab, ab_encoded, proto_factory)
    end = time.time()
    print("decode\t-> {}".format(end - start))


def main():
    n = 100000

    print("binary protocol struct benchmark for {} times:".format(n))
    encode(n)
    decode(n)

    print("\naccelerated protocol struct benchmark for {} times:".format(n))
    encode(n, TBinaryProtocolAcceleratedFactory())
    decode(n, TBinaryProtocolAcceleratedFactory())


if __name__ == "__main__":
    main()
