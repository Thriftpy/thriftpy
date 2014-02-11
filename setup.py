from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name='thriftpy',
    version=version,
    description='Thrift python lib reworked.',
    keywords='thrift python thriftpy',
    author='Lx Yu',
    author_email='i@lxyu.net',
    packages=find_packages(),
    entry_points={},
    url='http://lxyu.github.io/thriftpy/',
    license="MIT",
    zip_safe=False,
    long_description=open('README.rst').read(),
)
