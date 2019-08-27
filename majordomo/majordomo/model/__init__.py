# coding=utf-8
# __author__ = 'Mio'
from contextlib import contextmanager
from datetime import datetime

# import asyncpg
# from asyncpg.pool import Pool
from redis import Redis
from tornado.log import app_log
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

# from majordomo.settings import DB_PASSWORD, DB_USER, DB_DATABASE, DB_HOST
from majordomo.settings import session_factory as _session_factory, engine

# class DBPool:
#     _instance = None
#     @classmethod
#     async def make_pool(cls):
#         if not cls._instance:
#             cls._instance = await asyncpg.create_pool(
#                 host=DB_HOST, database=DB_DATABASE, user=DB_USER, password=DB_PASSWORD
#             )
#         return cls._instance
#
#     @property
#     def pool(self) -> Pool:
#         return self._instance
#
#
# # dbpool = DBPool()
redis = Redis()


@contextmanager
def make_session(session_factory=_session_factory) -> Session:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        app_log.error(e)
        raise
    finally:
        session.close()


class TimestampModel(object):
    """
    自带两个时间戳字段的base model
    """
    id = Column(Integer, primary_key=True, autoincrement=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mysql_charset = 'utf8'

    @classmethod
    def filter(cls, session_obj, *args):
        """
        类似Django-ORM风格的查询
        用法 SomeModel.filter(session, field==some_value)
        """
        return session_obj.query(cls).filter(*args)


Base = declarative_base(cls=TimestampModel)
Base.metadata.create_all(engine)
