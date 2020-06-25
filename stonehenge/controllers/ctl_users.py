from aiopg.sa import SAConnection
from aiopg.sa.result import RowProxy
from typing import Optional
import logging
import psycopg2
import psycopg2.errors
import aiohttp_session

from stonehenge.utils.type_helper import *

logger = logging.getLogger(__name__)


class UserInformation:
    __slots__ = ('id', 'login', 'mission', 'level')
    query = '''
    select u.*, sm.level_id as level from app_users u
    left join app_student_meta sm on u.student_meta_id = sm.id
    where u.id = %s;
    '''

    def __init__(self, row_db):
        for k in self.__slots__:
            self.__setattr__(k, row_db.get(k))


async def select_user_by_id(conn: SAConnection, key: int) -> 'Optional[UserInformation]':
    if key is None:
        return None

    if res := await (await conn.execute(UserInformation.query, (key,))).fetchone():
        return UserInformation(res)


async def select_all_users(conn: SAConnection) -> RowProxy:
    return await (
        await conn.execute('''
            select login, mission, auth_type from app_users
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
            res = await conn.execute('''
            select create_new_user(
                %s, -- cur_login
                %s, -- cur_email
                %s, -- cur_first_name
                %s, -- cur_last_name
                %s, -- cur_mission
                %s, -- cur_password
                %s, -- google_user
                %s -- vk_user
            );''', (login, email, first_name, last_name, mission,
                    password, google_user, vk_user))  # type: ResultProxy
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


async def prepare_index_page_for_teacher(conn: SAConnection, user_id: int):
    # get count of created tests
    created_tests = (await (await conn.execute('''
    select count(*) from app_tests t
    where t.author = %s''', (user_id,))).fetchone())[0]

    # get count of solution received
    sol_received = (await (await conn.execute('''
    select count(*) from app_marks
    inner join app_tests t on app_marks.test = t.id
    where t.author = %s;
    ''', (user_id,))).fetchone())[0]

    return {
        'created_tests': created_tests,
        'sol_received': sol_received,
    }


async def get_levels(conn: SAConnection):  # todo: transport to other file
    return list(await (await conn.execute('''
        select name from app_levels
        order by force;
        ''')).fetchall())


class AlreadyRegistered(Exception):
    pass
