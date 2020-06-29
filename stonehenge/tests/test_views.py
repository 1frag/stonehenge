from pytest_aiohttp import aiohttp_client


async def test_view(client: aiohttp_client) -> None:
    resp = await client.get('/')  # todo: make hinting for fixtures

    assert resp.status == 200


async def test_execute_anything():
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
