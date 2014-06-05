import time

from thriftpy.protocol import binary, cybinary


def benchmark(proto, n):
    start = time.time()
    bs = [proto.pack_i8(123) for _ in range(n)]
    mid = time.time()
    [proto.unpack_i8(b) for b in bs]
    end = time.time()
    print("pack_i8  \t-> {}".format(mid - start))
    print("unpack_i8\t-> {}".format(end - mid))

    start = time.time()
    bs = [proto.pack_i16(12345) for _ in range(n)]
    mid = time.time()
    [proto.unpack_i16(b) for b in bs]
    end = time.time()
    print("pack_i16\t-> {}".format(mid - start))
    print("unpack_i16\t-> {}".format(end - mid))

    start = time.time()
    bs = [proto.pack_i32(1234567890) for _ in range(n)]
    mid = time.time()
    [proto.unpack_i32(b) for b in bs]
    end = time.time()
    print("pack_i32\t-> {}".format(mid - start))
    print("unpack_i32\t-> {}".format(end - mid))

    start = time.time()
    bs = [proto.pack_i64(1234567890123456789) for _ in range(n)]
    mid = time.time()
    [proto.unpack_i64(b) for b in bs]
    end = time.time()
    print("pack_i64\t-> {}".format(mid - start))
    print("unpack_i64\t-> {}".format(end - mid))

    start = time.time()
    bs = [proto.pack_double(1234567890.1234567890) for _ in range(n)]
    mid = time.time()
    [proto.unpack_double(b) for b in bs]
    end = time.time()
    print("pack_double\t-> {}".format(mid - start))
    print("unpack_double\t-> {}".format(end - mid))


def main():
    n = 1000000

    print("binary protocol pack benchmark for {} times:".format(n))
    benchmark(binary, n)

    print("\ncybinary protocol pack benchmark for {} times:".format(n))
    benchmark(cybinary, n)


if __name__ == "__main__":
    main()
