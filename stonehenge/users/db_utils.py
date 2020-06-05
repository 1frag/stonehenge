from aiopg.sa import SAConnection
from aiopg.sa.result import RowProxy

from stonehenge.users.tables import users
from stonehenge.type_helper import *


__all__ = ['select_user_by_id', 'select_all_users']


async def select_user_by_id(conn: SAConnection, key: int) -> RowProxy:
    query = users\
        .select()\
        .where(users.c.id == key)\
        .order_by(users.c.id)
    cursor = await conn.execute(query)

    return await cursor.fetchone()


async def select_all_users(conn: SAConnection) -> RowProxy:
    query = users.select()
    cursor = await conn.execute(query)  # type: ResultProxy
    return await cursor.fetchmany()
