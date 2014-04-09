const i16 DEFAULT_LIST_SIZE = 10

typedef i32 timestamp

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
    4: optional timestamp created_at,
}

struct AddressBook {
    1: optional map<string, Person> people,
}

service AddressBookService {
    bool ping();
    bool add(1: Person person);
    bool delete(1: string name);
    Person get(1: string name);
    AddressBook book();
    map<PhoneType, string> get_phones(1: string name);
}
