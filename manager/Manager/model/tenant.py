# coding=utf-8
# __author__ = 'Mio'
from sqlalchemy import Column, Integer, String, Sequence

from Manager.model import Base, make_session
# from Manager.model import dbpool as db, pool


# noinspection PyShadowingBuiltins
class Tenant(Base):
    __tablename__ = 'tenant'

    user_id = Column(Integer, Sequence('user_id_seq'), index=True, unique=True, nullable=False)
    password = Column(String(length=64))
    user_name = Column(String(length=30))
    network_id = Column(String(length=64), comment="private network id")
    mysql_pw = Column(String(length=32), comment="user's common mysql password")

    def __repr__(self):
        return f"<Tenant(user_id={self.user_id},name={self.user_name})>"

    @classmethod
    def get_by_name(cls, name):
        with make_session() as s:
            return s.query(cls).filter_by(name=name).first()
    # @classmethod
    # async def async_new(cls, user_id, user_name, network_id=None) -> str:
    #     """
    #     insert or update on conflict
    #     :param user_id:
    #     :param user_name:
    #     :param network_id:
    #     :return:
    #     """
    #     return await db.pool.execute(f"""
    #     INSERT INTO "{cls.table_name}" (user_id, user_name, network_id)
    #     VALUE ({user_id}, '{user_name}', '{network_id}')
    #     ON CONFLICT (user_id) DO UPDATE
    #     set network_id='{network_id}'
    #     """)
    #
    # @classmethod
    # async def async_get_by_user_id(cls, user_id):
    #     return await db.pool.fetchrow(f"""SELECT * FROM "{cls.table_name}" WHERE user_id={user_id}""")
    #
    # @classmethod
    # async def async_get_by_name(cls, user_name):
    #     return await db.pool.fetchrow(f"""SELECT * FROM "{cls.table_name}" WHERE user_name='{user_name}'""")
    #
    # @classmethod
    # async def async_set_network_id(cls, user_id, network_id):
    #     return await db.pool.execute(f"""
    #         update "{cls.table_name}" set network_id='{network_id}' where user_id={user_id}
    #         """)

