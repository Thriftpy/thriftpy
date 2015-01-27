struct Grass {
    1: string name,
    2: string category
}


struct Sheep {
    1: string name,
    2: i32 age
}

struct Lion {
    1: string name,
    2: string home
}


service Eating {
    void ping(),
    Sheep eat_sheep(1: Lion tom),
    Grass eat_grass(1: Sheep sh),
    string eat(1: Lion l),
    i32 get_age(1: Sheep john)
}
