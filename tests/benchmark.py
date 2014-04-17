import time

from thriftpy.protocol import binary

import addressbook_thrift as addressbook
# import addressbook


def encode(n):
    for i in range(n):
        phone1 = addressbook.PhoneNumber()
        phone1.type = addressbook.PhoneType.MOBILE
        phone1.number = b'555-1212'
        phone2 = addressbook.PhoneNumber()
        phone2.type = addressbook.PhoneType.HOME
        phone2.number = b'555-1234'
        person = addressbook.Person()
        person.name = b"Alice"
        person.phones = [phone1, phone2]
        person.created_at = int(time.time())

        ab = addressbook.AddressBook()
        ab.people = {person.name: person}

        binary.write_output(binary.STRUCT, ab, ab.thrift_spec)


def main():
    start = time.time()
    encode(10000)
    end = time.time()
    print(end - start)


if __name__ == "__main__":
    main()
