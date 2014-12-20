enum Country {
    US = 1,
    UK = 2,
    CA = 3,
}

struct Person {
    1: string name,
    2: i32 age
    3: Country country = Country.US
}
