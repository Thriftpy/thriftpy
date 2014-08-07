#! /bin/sh


if ! which gunicorn_thrift > /dev/null; then
    echo "This example needs gunicorn_thrift installed:"
    echo "Ensure you have wheel installed before installing it"
    echo "$ pip install gunicorn_thrift"
    exit 1
fi

echo "available workers are: thriftpy_sync and thriftpy_gevent, using thriftpy_gevent"

gunicorn_thrift -c gunicorn_config.py ping_app:app
