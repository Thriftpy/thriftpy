import time

from thriftpy.protocol.binary import (
    pack_i8,
    pack_i16,
    pack_i32,
    pack_i64,
    pack_double,
    unpack_i8,
    unpack_i16,
    unpack_i32,
    unpack_i64,
    unpack_double,
)


def benchmark(n):
    print("Benchmark pack/unpack for {} times.".format(n))

    start = time.time()
    bs = [pack_i8(123) for _ in range(n)]
    mid = time.time()
    l = [unpack_i8(b) for b in bs]
    end = time.time()
    print("pack_i8  \t-> {}".format(mid - start))
    print("unpack_i8\t-> {}".format(end - mid))
    assert 123 == l[0]

    start = time.time()
    bs = [pack_i16(12345) for _ in range(n)]
    mid = time.time()
    l = [unpack_i16(b) for b in bs]
    end = time.time()
    print("pack_i16\t-> {}".format(mid - start))
    print("unpack_i16\t-> {}".format(end - mid))
    assert 12345 == l[0]

    start = time.time()
    bs = [pack_i32(1234567890) for _ in range(n)]
    mid = time.time()
    l = [unpack_i32(b) for b in bs]
    end = time.time()
    print("pack_i32\t-> {}".format(mid - start))
    print("unpack_i32\t-> {}".format(end - mid))
    assert 1234567890 == l[0]

    start = time.time()
    bs = [pack_i64(1234567890123456789) for _ in range(n)]
    mid = time.time()
    l = [unpack_i64(b) for b in bs]
    end = time.time()
    print("pack_i64\t-> {}".format(mid - start))
    print("unpack_i64\t-> {}".format(end - mid))
    assert 1234567890123456789 == l[0]

    start = time.time()
    bs = [pack_double(1234567890.1234567890) for _ in range(n)]
    mid = time.time()
    l = [unpack_double(b) for b in bs]
    end = time.time()
    print("pack_double\t-> {}".format(mid - start))
    print("unpack_double\t-> {}".format(end - mid))
    assert 1234567890.1234567890 == l[0]


if __name__ == "__main__":
    benchmark(1000000)
