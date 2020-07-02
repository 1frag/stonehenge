import pytest
from pytest_aiohttp import aiohttp_client
from aiopg.sa import SAConnection


async def test_index_view(app, aiohttp_client) -> None:
    client = await aiohttp_client(app)
    resp = await client.get('/', timeout=1)

    assert resp.status == 200


async def test_execute_in_db():
    """
    Use:
    from stonehenge.tests.test_views import test_execute_anything
    db_state = test_execute_anything()
    conn = await db_state.__anext__()
    ...
    await db_state.__anext__()
    """
    import aiopg.sa
    from stonehenge.utils.common import get_config

    db = await aiopg.sa.create_engine(
        **get_config()['postgres']
    )  # type: aiopg.sa.engine.Engine
    conn = await db.acquire()  # type: aiopg.sa.connection.SAConnection
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_check_user_table(conn: SAConnection):
    q1 = await conn.execute('''
        insert into app_users (login, first_name, last_name, email,
            mission, auth_type)
        values (%s, %s, %s, %s, %s, %s)
        returning id;
    ''', ('test_login', 'test_first_name', 'test_last_name',
          'test_email', 'student', 'google'))
    user_id = await q1.fetchone()

    q2 = await conn.execute('''
    select login, first_name, last_name from app_users
    where id=%s
    ''', (user_id, ))
    user = await q2.fetchone()
    assert user['login'] == 'test_login'
    assert user['first_name'] == 'test_first_name'
    assert user['last_name'] == 'test_last_name'
