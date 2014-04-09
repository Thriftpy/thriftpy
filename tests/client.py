import time

from thriftpy.rpc import make_client

import addressbook_thrift as addressbook


def main():
    client = make_client(addressbook.AddressBookService, '127.0.0.1', 8000)
    print("ping() -> {}".format(client.ping()))

    phone1 = addressbook.PhoneNumber()
    phone1.type = addressbook.PhoneType.MOBILE
    phone1.number = '555-1212'
    phone2 = addressbook.PhoneNumber()
    phone2.type = addressbook.PhoneType.HOME
    phone2.number = '555-1234'
    person = addressbook.Person()
    person.name = "Alice"
    person.phones = [phone1, phone2]
    person.created_at = int(time.time())
    print("add({}) -> {}".format(person, client.add(person)))

    name = "Alice"
    print("get({}) -> {}".format(name, client.get(name)))

    print("get_phones({}) -> {}".format(name, client.get_phones(name)))

    print("book() -> {}".format(client.book()))


if __name__ == "__main__":
    main()
