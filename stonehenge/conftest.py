import pytest
from sqlalchemy import create_engine
import aiopg.sa


from stonehenge.utils.common import PATH, get_config
from stonehenge.utils.common import get_db_url


TEST_CONFIG_PATH = PATH / 'config' / 'api.test.yml'
CONFIG_PATH = PATH / 'config' / 'api.dev.yml'

test_config = get_config(test=True, readable=True)


async def setup_test_db(engine) -> None:
    """
    Removing the old test database environment and creating new clean
    environment.
    """
    # test params
    db_name = test_config['postgres']['database']
    db_user = test_config['postgres']['user']
    db_password = test_config['postgres']['password']

    async with engine.acquire() as conn:
        await conn.execute(
            f"create user {db_user} with password '{db_password}'"
        )
        await conn.execute(
            f"create database {db_name} encoding 'UTF8'"
        )
        await conn.execute(
            f"grant all privileges on database {db_name} to {db_user}"
        )


async def teardown_test_db(engine) -> None:
    """
    Removing the test database environment.
    """
    # test params
    db_name = test_config['postgres']['database']
    db_user = test_config['postgres']['user']

    async with engine.acquire() as conn:
        await conn.execute(
            f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid();
            """
        )
        await conn.execute(f"drop database if exists {db_name}")
        await conn.execute(f"drop role if exists {db_user}")


# fixtures
@pytest.fixture
async def db():
    print('when False:' + get_db_url(test=False)['dsn'])
    print('when True:' + get_db_url(test=True)['dsn'])
    real_engine = await aiopg.sa.create_engine(
        get_db_url(test=False)['dsn'],
    )
    await teardown_test_db(real_engine)
    await setup_test_db(real_engine)

    test_engine = await aiopg.sa.create_engine(
        get_db_url(test=True)['dsn'],
    )
    async with test_engine.acquire() as conn:
        with open('./db_state/migrate.sql') as m:
            await conn.execute(m.read())
    yield test_engine
    # await teardown_test_db(real_engine)


@pytest.fixture
async def conn(db) -> aiopg.sa.SAConnection:
    async with db.acquire() as conn:
        yield conn


@pytest.fixture
def app():
    from stonehenge.application.app import init_app
    yield init_app(True)
