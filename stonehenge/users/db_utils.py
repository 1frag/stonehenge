from aiopg.sa import SAConnection
from aiopg.sa.result import RowProxy
from typing import Union, Optional
import logging
import psycopg2
import psycopg2.errors
import aiohttp_session
import aiohttp.web

from stonehenge.type_helper import *

logger = logging.getLogger(__name__)


async def select_user_by_id(conn: SAConnection, key: int) -> RowProxy:
    return await (
        await conn.execute('''
        select (login, mission, auth_type) from app_users
        where id = %d
    ''', (key,))
    ).fetchone()


async def select_all_users(conn: SAConnection) -> RowProxy:
    return await (
        await conn.execute('''
            select (login, mission, auth_type) from app_users
        ''')
    ).fetchmany()


async def create_user(
        conn: SAConnection, *,
        login: str,
        email: str,
        first_name: str,
        last_name: str,
        mission: str,
        password: Optional[str] = None,
        google_user: Optional[int] = None,
        vk_user: Optional[int] = None,
) -> int:
    pwd_way = [password is None, google_user is None, vk_user is None]
    if sum(pwd_way) != 2:
        logger.error('Incorrect usage of create_user function. Use'
                     f'only one way to authenticate user {pwd_way=}', )
        raise Exception('incorrect pwd_way')

    if mission not in ('student', 'teacher', 'advertiser'):
        logger.error(f'Incorrect mission type {mission=}')
        raise Exception('incorrect mission')

    if google_user or vk_user:
        trans = None
        try:
            trans = await conn.begin()  # type: Optional[RootTransaction]
            if google_user:
                res = await conn.execute('''
                insert into app_google_users (google_id)
                values (%s);
                insert into app_users (login, first_name, last_name, email, google_id,
                mission, auth_type)
                values (%s, %s, %s, %s, %s, %s, 'google')
                returning id;
                ''', google_user, login, first_name, last_name, email,
                                         google_user, mission)  # type: ResultProxy
            else:
                res = await conn.execute('''
                insert into app_vk_users (vk_id)
                values (%s);
                insert into app_users (login, first_name, last_name, email, vk_id,
                mission, auth_type)
                values (%s, %s, %s, %s, %s, %s, 'vk')
                returning id;
                ''', vk_user, login, first_name, last_name, email,
                                         vk_user, mission)  # type: ResultProxy
            ret_id = await res.fetchone()  # type: RowProxy
            await trans.commit()
            return ret_id[0]
        except psycopg2.Error as e:
            if trans:
                logger.error(f'{e.pgcode=}')
                await trans.rollback()
            if psycopg2.errors.lookup(e.pgcode).__name__ == 'UniqueViolation':
                logger.error(f'{e.pgcode=}, {e.pgerror=}')
                raise AlreadyRegistered() from None
            raise e
    else:
        logger.error(f'{pwd_way=}')
        raise NotImplementedError()


async def get_user_by_google(conn: SAConnection, google_user_id: int):
    return (await (await conn.execute('''
    select id from app_users
    where google_id = %s;
    ''', (google_user_id,))).fetchone())[0]


async def get_user_by_vk(conn: SAConnection, vk_user_id: int):
    return (await (await conn.execute('''
    select id from app_users
    where vk_id = %s;
    ''', (vk_user_id,))).fetchone())[0]


async def remember_user(request: 'Request', user_id: int):
    session = await aiohttp_session.get_session(request)
    session['user_id'] = user_id


class AlreadyRegistered(Exception):
    pass
