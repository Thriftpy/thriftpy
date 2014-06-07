thriftpy vs apache thrift
=========================

The addressbook struct benchmark based on addressbook.thrift.

The Apache Thrift SDK is generated with::

    thrift --gen py:new_style,utf8strings -out ./ addressbook.thrift

The benchmarks are run in my rMBP 15 late 2013 edition.


Apache Thrift
-------------

python2.7.6::

    binary protocol struct benchmark for 100000 times:
    encode  -> 3.74061203003
    decode  -> 5.02829790115

    accelerated protocol struct benchmark for 100000 times:
    encode  -> 0.398949146271
    decode  -> 0.536000013351

ThriftPy
--------

pypy2.3::

    binary protocol struct benchmark for 100000 times:
    encode  -> 0.413738965988
    decode  -> 0.605606079102

python2.7.6::

    binary protocol struct benchmark for 100000 times:
    encode  -> 3.356539011
    decode  -> 4.65092682838

    cybinary protocol struct benchmark for 100000 times:
    encode  -> 1.20373010635
    decode  -> 2.18114209175

python3.4.1 + thriftpy::

    binary protocol struct benchmark for 100000 times:
    encode  -> 3.291545867919922
    decode  -> 4.337666034698486

    cybinary protocol struct benchmark for 100000 times:
    encode  -> 1.1233220100402832
    decode  -> 1.9023690223693848

-----------------------------------

thriftpy pack benchmark:

pypy2.3::

    binary protocol pack benchmark for 1000000 times.
    pack_i8         -> 0.0132279396057
    unpack_i8       -> 0.0130062103271
    pack_i16        -> 0.0206890106201
    unpack_i16      -> 0.0133810043335
    pack_i32        -> 0.0172791481018
    unpack_i32      -> 0.0111408233643
    pack_i64        -> 0.0175950527191
    unpack_i64      -> 0.0128269195557
    pack_double     -> 0.092297077179
    unpack_double   -> 0.0423738956451


python 3.4.1::

    binary protocol pack benchmark for 1000000 times.
    pack_i8         -> 0.31328296661376953
    unpack_i8       -> 0.3058948516845703
    pack_i16        -> 0.3236830234527588
    unpack_i16      -> 0.3343539237976074
    pack_i32        -> 0.32091307640075684
    unpack_i32      -> 0.33921098709106445
    pack_i64        -> 0.34093785285949707
    unpack_i64      -> 0.3671731948852539
    pack_double     -> 0.3190128803253174
    unpack_double   -> 0.3318800926208496

    cybinary protocol pack benchmark for 1000000 times.
    pack_i8         -> 0.14059996604919434
    unpack_i8       -> 0.0897068977355957
    pack_i16        -> 0.16286921501159668
    unpack_i16      -> 0.12385988235473633
    pack_i32        -> 0.17861008644104004
    unpack_i32      -> 0.12960481643676758
    pack_i64        -> 0.18740415573120117
    unpack_i64      -> 0.14306282997131348
    pack_double     -> 0.17037487030029297
    unpack_double   -> 0.11780405044555664


python 2.7.6::

    binary protocol pack benchmark for 1000000 times:
    pack_i8         -> 0.372659921646
    unpack_i8       -> 0.305228948593
    pack_i16        -> 0.354794025421
    unpack_i16      -> 0.316354990005
    pack_i32        -> 0.362054109573
    unpack_i32      -> 0.314528942108
    pack_i64        -> 0.365602970123
    unpack_i64      -> 0.325259923935
    pack_double     -> 0.325922012329
    unpack_double   -> 0.330043077469

    cybinary protocol pack benchmark for 1000000 times:
    pack_i8         -> 0.134818077087
    unpack_i8       -> 0.0831379890442
    pack_i16        -> 0.161223888397
    unpack_i16      -> 0.0890259742737
    pack_i32        -> 0.179952144623
    unpack_i32      -> 0.0975089073181
    pack_i64        -> 0.184626102448
    unpack_i64      -> 0.0943579673767
    pack_double     -> 0.179758071899
    unpack_double   -> 0.0928230285645
