import time

from thriftpy.utils import serialize, deserialize

import addressbook_thrift as addressbook


start = time.time()
for i in range(10000):
    n = addressbook.PhoneNumber()
    n.type = 0
    n.number = "123456"
    b = serialize(n)
    deserialize(addressbook.PhoneNumber(), b)
end = time.time()

print(end - start)
