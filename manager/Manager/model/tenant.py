# coding=utf-8
# __author__ = 'Mio'
from asyncpg.pool import Pool

from Manager.model import dbpool as db


# noinspection PyShadowingBuiltins
class TenantTable:
    table_name = 'tenant'
    fields = [
        'id', 'user_id', 'user_name', 'network_id',
        'create_time', 'update_time',
    ]

    @classmethod
    async def new(cls, user_id, user_name, network_id=None) -> str:
        """
        insert or update on conflict
        :param user_id:
        :param user_name:
        :param network_id:
        :return:
        """
        return await db.pool.execute(f"""
        INSERT INTO "{cls.table_name}" (user_id, user_name, network_id) 
        VALUE ({user_id}, '{user_name}', '{network_id}')
        ON CONFLICT (user_id) DO UPDATE
        set network_id='{network_id}'
        """)

    @classmethod
    async def get_by_user_id(cls, user_id):
        return await db.pool.fetchrow(f"""SELECT * FROM "{cls.table_name}" WHERE user_id={user_id}""")

    @classmethod
    async def get_by_name(cls, user_name):
        return await db.pool.fetchrow(f"""SELECT * FROM "{cls.table_name}" WHERE user_name='{user_name}'""")

    @classmethod
    async def set_network_id(cls, user_id, network_id):
        return await db.pool.execute(f"""
            update "{cls.table_name}" set network_id='{network_id}' where user_id={user_id}
            """)
