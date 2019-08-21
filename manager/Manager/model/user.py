# coding=utf-8
# __author__ = 'Mio'

from Manager.model import dbpool


# noinspection PyShadowingBuiltins
class User:
    table_name = 'user'

    @classmethod
    async def get(cls, id):
        async with dbpool.pool.acquire() as con:
            return await con.fetchrow(f"""SELECT * FROM "{cls.table_name}" WHERE id={id}""")

    @classmethod
    async def get_by_name(cls, name):
        async with dbpool.pool.acquire() as con:
            return await con.fetchrow(f"""SELECT * FROM "{cls.table_name}" WHERE name='{name}'""")

    @classmethod
    async def get_by_token(cls, token):
        async with dbpool.pool.acquire() as con:
            return await con.fetchrow(f"""SELECT * FROM "{cls.table_name}" WHERE token='{token}'""")

    @classmethod
    async def set_token(cls, id, token):
        async with dbpool.pool.acquire() as con:
            return await con.fetchrow(f"""
            update "{cls.table_name}" set token='{token}' where id={id}
            """)

    @classmethod
    async def get_by_user_id(cls, user_id):
        async with dbpool.pool.acquire() as con:
            return await con.fetchrow(f"""SELECT * FROM "{cls.table_name}" WHERE user_id='{user_id}'""")

