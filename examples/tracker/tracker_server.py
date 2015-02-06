# -*- coding: utf-8 -*-


import argparse
from stuffs import server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default=34567, type=int, help="port")

    args = parser.parse_args()
    server(port=args.port).serve()


if __name__ == "__main__":
    main()
