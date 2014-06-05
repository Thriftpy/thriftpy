enum PhoneType {
    MOBILE,
    HOME,
    WORK,
}

struct PhoneNumber {
    1: optional PhoneType type,
    2: optional string number,
}

struct Person {
    1: optional string name,
    2: optional list<PhoneNumber> phones,
}

typedef map<string, Person> PersonMap

struct AddressBook {
    1: optional PersonMap people,
}
