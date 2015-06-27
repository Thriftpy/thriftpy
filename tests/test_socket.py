# -*- coding: utf-8 -*-

import pytest

from thriftpy.transport.socket import TSocket, TServerSocket
from thriftpy.transport import TTransportException


def test_close():
    server = TServerSocket(host="localhost", port=12345)
    client = TSocket(host="localhost", port=12345)

    server.listen()
    client.open()

    c = server.accept()

    client.close()

    with pytest.raises(TTransportException) as e:
        c.read(1024)
    assert "TSocket read 0 bytes" in e.value.message

    c.write(b"world")
    c.close()

    assert c.handle is None
