Calculator Example (Using namespace importer)
=============================================

### Installation & Running

You may want to create a virtual environment and later remove it if you don't want
this to interfere with your python packages.

```bash
$ pip install .
$ calculator-server
```

Interact with the running server.

```python
>>> import example
>>> with example.client() as client:
>>>     client.ping()
>>>     for x in range(1, 1000):
>>>         client.add(x, x*2)
>>>
```
