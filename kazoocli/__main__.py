#!/usr/bin/env python

# Copyright (C) 2015 Maxime Petazzoni <maxime.petazzoni@bulix.org>

import argparse
import logging
import sys

from . import kazoocli
from .version import description


def main(args=None):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('server', nargs='?',
                        help='The ZooKeeper server to connect to',
                        default='localhost:2181')
    parser.add_argument('-D', '--debug', action='store_const',
                        const=logging.DEBUG, default=logging.ERROR,
                        help='Enable debug logging of Kazoo')
    options = parser.parse_args(args=args)

    logging.basicConfig(stream=sys.stderr, level=options.debug)
    try:
        kazoocli.KazooCli(options.server)
        return 0
    except:
        if options.debug == logging.DEBUG:
            raise
        print(sys.exc_info()[1])
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
