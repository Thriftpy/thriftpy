clean:
	rm -vf thriftpy/protocol/cybin/*.c thriftpy/protocol/*.so
	rm -vf thriftpy/transport/*.c thriftpy/transport/*.so
	rm -vf thriftpy/transport/*/*.c thriftpy/transport/*/*.so
	rm -vf dist/*

build_ext: clean
	python setup.py build_ext

package: build_ext
	python setup.py sdist

upload: build_ext
	python setup.py sdist upload

.PHONY: package upload
