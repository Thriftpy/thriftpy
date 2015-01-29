# -*- coding: utf-8 -*-


from stuffs import client, thrift


def main():
    lion = thrift.Lion(name="jerry", home="africa")
    with client() as c:
        c.eat(lion)


if __name__ == "__main__":
    main()
