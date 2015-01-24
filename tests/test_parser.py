# coding=utf8

from thriftpy.parser import load
from thriftpy.parser.exc import ThriftParserError


def test_comments():
    load('parser-cases/comments.thrift')


def test_constants():
    thrift = load('parser-cases/constants.thrift')
    assert thrift.int16 == 3
    assert thrift.int32 == 800
    assert thrift.int64 == 123456789
    assert thrift.tstr == 'hello world'
    assert thrift.integer32 == 900
    assert thrift.tdouble == 1.3
    assert thrift.tlist == [1, 2, 3]
    assert thrift.tset == set([1, 2, 3])
    assert thrift.tmap1 == {'key': 'val'}
    assert thrift.tmap2 == {'key': 32}
    assert thrift.my_country == 4
    assert thrift.tom == thrift.Person(name='tom')
    assert thrift.country_map == {1: 'US', 2: 'UK', 3: 'CA', 4: 'CN'}


def test_include():
    thrift = load('parser-cases/include.thrift', include_dir='./parser-cases')
    assert thrift.datetime == 1422009523


def test_tutorial():
    thrift = load('parser-cases/tutorial.thrift', include_dir='./parser-cases')
    assert thrift.INT32CONSTANT == 9853
    assert thrift.MAPCONSTANT == {'hello': 'world', 'goodnight': 'moon'}
    assert thrift.Operation.ADD == 1 and thrift.Operation.SUBTRACT == 2 \
        and thrift.Operation.MULTIPLY == 3 and thrift.Operation.DIVIDE == 4
    work = thrift.Work()
    assert work.num1 == 0 and work.num2 is None and work.op is None \
        and work.comment is None
    assert set(thrift.Calculator.thrift_services) == set([
        'ping', 'add', 'calculate', 'zip', 'getStruct'])


def test_e_type_error():
    try:
        load('parser-cases/e_type_error_0.thrift')
    except ThriftParserError as e:
        assert 'Type error' in str(e)
    try:
        load('parser-cases/e_type_error_1.thrift')
    except ThriftParserError as e:
        assert 'Type error' in str(e)

    try:
        load('parser-cases/e_type_error_2.thrift')
    except ThriftParserError as e:
        assert 'Type error' in str(e)


def test_value_ref():
    thrift = load('parser-cases/value_ref.thrift')
    assert thrift.container == {'key': [1, 2, 3]}
    assert thrift.lst == [39, 899, 123]


def test_type_ref():
    thrift = load('parser-cases/type_ref.thrift')
    assert thrift.jerry == thrift.type_ref_shared.Writer(
        name='jerry', age=26, country=thrift.type_ref_shared.Country.US)
