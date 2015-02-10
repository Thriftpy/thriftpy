# -*- coding: utf-8 -*-


import code
from stuffs import client, thrift


def main():
    with client() as c:
        code.interact(local={'c': c, 't': thrift})


if __name__ == "__main__":
    main()
