# coding=utf-8
# __author__ = 'Mio'
from os import getenv

import tornado.ioloop
import uvloop

DATA_PATH_PREFIX = getenv('DATA_PATH_PREFIX', '/data')
WP_IMAGE_NAME = getenv('WP_IMAGE_NAME', 'mio-wp')

uvloop.install()
ioloop = tornado.ioloop.IOLoop.current()
