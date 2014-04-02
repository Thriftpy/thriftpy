def setup():
    from .parser import ThriftImporter
    ThriftImporter().install()

setup()
del setup
