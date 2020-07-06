import pytest
from pytest_aiohttp import aiohttp_client
from aiopg.sa import SAConnection


async def test_index_view(app, aiohttp_client) -> None:
    client = await aiohttp_client(app)
    resp = await client.get('/', timeout=1)

    assert resp.status == 200


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
    assert user_id is not None

    q2 = await conn.execute('''
    select login, first_name, last_name from app_users
    where id=%s
    ''', (user_id, ))
    user = await q2.fetchone()
    assert user['login'] == 'test_login'
    assert user['first_name'] == 'test_first_name'
    assert user['last_name'] == 'test_last_name'


async def test_when_user_unauthorized(app, aiohttp_client):
    # получение объекта клиента
    client = await aiohttp_client(app)
    # выполнение web запроса
    resp = await client.get('/')
    # проверка конечного адреса (после редиректов)
    assert resp.real_url.path == '/login'
