#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import example


def main():
    logging.info('Listening on %s:%s...', example.HOST, example.PORT)
    try:
        example.server.serve()
    except KeyboardInterrupt:
        example.server.close()
