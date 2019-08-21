# coding=utf-8
# __author__ = 'Mio'

import asyncpg
from redis import Redis


class DBPool:
    _instance = None
    @classmethod
    async def make_pool(cls):
        if not cls._instance:
            cls._instance = await asyncpg.create_pool(
                host='localhost', database='moto', user='postgres', password='postgres'
            )
        return cls._instance

    @property
    def pool(self):
        return self._instance


dbpool = DBPool()

redis = Redis()
