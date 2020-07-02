import pytest


async def helper_execute_in_db():
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
