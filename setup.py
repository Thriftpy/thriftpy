from setuptools import setup, find_packages

# Keep this in lockstep with the pinned thriftpy2 dependency below, thriftpy is
# a thin compatibility shim and every release tracks the thriftpy2 it wraps.
version = "0.6.0"

install_requires = [
    "thriftpy2==%s" % version,
]

setup(name="thriftpy",
      version=version,
      description="Compatibility shim that exposes thriftpy2 under the "
                  "historical thriftpy name.",
      keywords="thrift python thriftpy thriftpy2",
      author="Lx Yu",
      author_email="i@lxyu.net",
      packages=find_packages(exclude=['benchmark', 'docs', 'tests']),
      entry_points={},
      url="https://github.com/Thriftpy/thriftpy",
      license="MIT",
      zip_safe=False,
      long_description=open("README.rst").read(),
      install_requires=install_requires,
      python_requires='>=3.7',
      classifiers=[
          "Topic :: Software Development",
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: Implementation :: PyPy",
      ])
