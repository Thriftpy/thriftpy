from thriftpy.rpc import make_server

import addressbook_thrift as addressbook


class Dispatcher(object):
    def __init__(self):
        self.ab = addressbook.AddressBook()
        self.ab.people = {}

    def ping(self):
        return True

    def add(self, person):
        self.ab.people[person.name] = person
        return True

    def delete(self, name):
        self.ab.people.pop(name)
        return True

    def get(self, name):
        return self.ab.people[name]

    def book(self):
        return self.ab

    def get_phones(self, name):
        phone_numbers = self.ab.people[name].phones
        return {p.type: p.number for p in phone_numbers}


def main():
    server = make_server(addressbook.AddressBookService, Dispatcher(),
                         '127.0.0.1', 8000)
    print("serving...")
    server.serve()


if __name__ == "__main__":
    main()
