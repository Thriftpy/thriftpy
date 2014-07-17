import time

import thriftpy
from thriftpy.utils import serialize, deserialize
from thriftpy.protocol import TBinaryProtocolFactory, TCyBinaryProtocolFactory

addressbook = thriftpy.load("addressbook.thrift")


def make_addressbook():
    phone1 = addressbook.PhoneNumber()
    phone1.type = addressbook.PhoneType.MOBILE
    phone1.number = b'555-1212'
    phone2 = addressbook.PhoneNumber()
    phone2.type = addressbook.PhoneType.HOME
    phone2.number = b'555-1234'
    person = addressbook.Person()
    person.name = b"Alice"
    person.phones = [phone1, phone2]
    person.created_at = 1400000000

    ab = addressbook.AddressBook()
    ab.people = {person.name: person}
    return ab
ab_encoded = serialize(make_addressbook())


def encode(n, proto_factory=TBinaryProtocolFactory()):
    ab = make_addressbook()
    start = time.time()
    for i in range(n):
        serialize(ab, proto_factory)
    end = time.time()
    print("encode\t-> {}".format(end - start))


def decode(n, proto_factory=TBinaryProtocolFactory()):
    ab = addressbook.AddressBook()
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

    print("\ncybin protocol struct benchmark for {} times:".format(n))
    encode(n, TCyBinaryProtocolFactory())
    decode(n, TCyBinaryProtocolFactory())


if __name__ == "__main__":
    main()
