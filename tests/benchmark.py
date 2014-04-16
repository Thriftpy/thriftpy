import time

from thriftpy.protocol import binary

import addressbook_thrift as addressbook
# import addressbook


start = time.time()
for i in range(10000):
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

end = time.time()

print(end - start)
