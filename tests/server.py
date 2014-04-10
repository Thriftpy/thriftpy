from thriftpy.rpc import make_server

import addressbook
# import addressbook_thrift as addressbook


class Dispatcher(object):
    def __init__(self):
        self.ab = addressbook.AddressBook()
        self.ab.people = {}

    def ping(self):
        return True

    def add(self, person):
        self.ab.people[person.name] = person
        return True

    def remove(self, name):
        try:
            self.ab.people.pop(name)
            return True
        except KeyError:
            raise addressbook.PersonNotExistsError(
                "{} not exists".format(name))

    def get(self, name):
        try:
            return self.ab.people[name]
        except KeyError:
            raise addressbook.PersonNotExistsError(
                "{} not exists".format(name))

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
