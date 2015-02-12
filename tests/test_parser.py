# -*- coding: utf-8 -*-

from thriftpy.thrift import TType
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
    assert thrift.book == thrift.type_ref_shared.Book(name='Hello World',
                                                      writer=thrift.jerry)


def test_e_value_ref():
    try:
        load('parser-cases/e_value_ref_0.thrift')
    except ThriftParserError as e:
        pass
    try:
        load('parser-cases/e_value_ref_1.thrift')
    except ThriftParserError as e:
        assert str(e) == 'No named enum value found named \'Lang.Python\''

    try:
        load('parser-cases/e_value_ref_2.thrift')
    except ThriftParserError as e:
        assert str(e) == \
            'No named enum value or constant found named \'Cookbook\''


def test_enums():
    thrift = load('parser-cases/enums.thrift')
    assert thrift.Lang.C == 0
    assert thrift.Lang.Go == 1
    assert thrift.Lang.Java == 2
    assert thrift.Lang.Javascript == 3
    assert thrift.Lang.PHP == 4
    assert thrift.Lang.Python == 5
    assert thrift.Lang.Ruby == 6
    assert thrift.Country.US == 1
    assert thrift.Country.UK == 2
    assert thrift.Country.CN == 3
    assert thrift.Country._named_values == set([1])
    assert thrift.OS.OSX == 0
    assert thrift.OS.Win == 3
    assert thrift.OS.Linux == 4
    assert thrift.OS._named_values == set([3])


def test_structs():
    thrift = load('parser-cases/structs.thrift')
    assert thrift.Person.thrift_spec == {
        1: (TType.STRING, 'name', False),
        2: (TType.STRING, 'address', False)
    }
    assert thrift.Person.default_spec == [
        ('name', None), ('address', None)
    ]
    assert thrift.Email.thrift_spec == {
        1: (TType.STRING, 'subject', False),
        2: (TType.STRING, 'content', False),
        3: (TType.STRUCT, 'sender', thrift.Person, False),
        4: (TType.STRUCT, 'recver', thrift.Person, True),
    }
    assert thrift.Email.default_spec == [
        ('subject', 'Subject'), ('content', None),
        ('sender', None), ('recver', None)
    ]
    assert thrift.email == thrift.Email(
        subject='Hello',
        content='Long time no see',
        sender=thrift.Person(name='jack', address='jack@gmail.com'),
        recver=thrift.Person(name='chao', address='chao@gmail.com')
    )


def test_e_structs():
    try:
        load('parser-cases/e_structs_0.thrift')
    except ThriftParserError as e:
        assert str(e) == \
            'Field \'name\' was required to create constant for type \'User\''

    try:
        load('parser-cases/e_structs_1.thrift')
    except ThriftParserError as e:
        assert str(e) == \
            'No field named \'avatar\' was found in struct of type \'User\''


def test_service():
    thrift = load('parser-cases/service.thrift')
    assert thrift.EmailService.thrift_services == ['ping', 'send']
    assert thrift.EmailService.ping_args.thrift_spec == {}
    assert thrift.EmailService.ping_args.default_spec == []
    assert thrift.EmailService.ping_result.thrift_spec == {
        1: (TType.STRUCT, 'network_error', thrift.NetworkError, False)
    }
    assert thrift.EmailService.ping_result.default_spec == [
        ('network_error', None)
    ]
    assert thrift.EmailService.send_args.thrift_spec == {
        1: (TType.STRUCT, 'recver', thrift.User, False),
        2: (TType.STRUCT, 'sender', thrift.User, False),
        3: (TType.STRUCT, 'email', thrift.Email, False),
    }
    assert thrift.EmailService.send_args.default_spec == [
        ('recver', None), ('sender', None), ('email', None)
    ]
    assert thrift.EmailService.send_result.thrift_spec == {
        0: (TType.BOOL, 'success', False),
        1: (TType.STRUCT, 'network_error', thrift.NetworkError, False)
    }
    assert thrift.EmailService.send_result.default_spec == [
        ('success', None), ('network_error', None)
    ]


def test_service_extends():
    thrift = load('parser-cases/service_extends.thrift')
    assert thrift.PingService.thrift_services == ['ping', 'getStruct']


def test_e_service_extends():
    try:
        load('parser-cases/e_service_extends_0.thrift')
    except ThriftParserError as e:
        assert 'Can\'t find service' in str(e)


def test_e_dead_include():
    try:
        load('parser-cases/e_dead_include_0.thrift')
    except ThriftParserError as e:
        assert 'Dead including' in str(e)
