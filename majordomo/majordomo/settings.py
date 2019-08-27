# coding=utf-8
# __author__ = 'Mio'
from os import getenv
from pathlib import Path

import docker
import tornado.ioloop
import uvloop
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Container
DATA_PATH_PREFIX = getenv('DATA_PATH_PREFIX', '/data')
WP_IMAGE_NAME = getenv('WP_IMAGE_NAME', 'mio-wp')
LOG_MAX_FILE = getenv('LOG_MAX_FILE', '1')
LOG_MAX_SIZE = getenv('LOG_MAX_SIZE', '10m')
REVERSE_PROXY_CONTAINER_NAME = getenv('REVERSE_PROXY_CONTAINER_NAME', 'traefik')
COMMON_DB_CONTAINER_NAME = getenv('COMMON_DB_CONTAINER_NAME', 'maria')
COMMON_DB_DATA_PATH = Path(getenv('COMMON_DB_DATA_PATH', '/data/maria'))
# TODO use docker secret
COMMON_DB_PW = getenv('COMMON_DB_PW', 'root')
# Database(PG) for moto
DB_HOST = getenv('DB_HOST', 'localhost')
DB_PORT = getenv('DB_PORT', 5432)
DB_DATABASE = getenv('DB_DATABASE', 'moto')
DB_USER = getenv('DB_USER', 'postgres')
DB_PASSWORD = getenv('DB_PASSWORD', 'postgres')
DB_CONN_CHARSET = getenv('DB_CONN_CHARSET', 'utf8')
DB_SQL_ECHO = bool(int(getenv('DB_SQL_ECHO', 0)))
DB_DSN = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
DB_CONNECT_STR = getenv(
    'DB_CONNECT_STR', f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}')

# CONN_POOL_RECYCLE_SECS = int(getenv("CONN_POOL_RECYCLE_SECS", 600))
engine = create_engine(
    DB_CONNECT_STR,
    echo=DB_SQL_ECHO,
    encoding=DB_CONN_CHARSET,
    pool_size=10,
    max_overflow=10,
    pool_recycle=3600,
    pool_timeout=10,
)
session_factory = sessionmaker(engine)
# Tornado
uvloop.install()
ioloop = tornado.ioloop.IOLoop.current()
# Docker
client = docker.from_env()
