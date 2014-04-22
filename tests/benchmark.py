import time

from io import BytesIO

from thriftpy.protocol import cybinary

import addressbook_thrift as addressbook
# import addressbook


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


def encode(n):
    for i in range(n):
        ab = make_addressbook()
        b = BytesIO()
        cybinary.write_val(b, cybinary.STRUCT, ab)


def decode(n):
    b = BytesIO()
    ab = make_addressbook()
    cybinary.write_val(b, cybinary.STRUCT, ab)
    encoded = b.getvalue()
    for i in range(n):
        b = BytesIO(encoded)
        cybinary.read_val(b, cybinary.STRUCT, addressbook.AddressBook)


def main():
    start = time.time()
    encode(10000)
    end = time.time()
    print(end - start)

    start = time.time()
    decode(10000)
    end = time.time()
    print(end - start)


if __name__ == "__main__":
    main()
