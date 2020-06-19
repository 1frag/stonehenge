import pytest
from sqlalchemy import create_engine
import aiopg.sa


from stonehenge.utils.common import PATH, get_config
from stonehenge.utils.common import get_db_url


TEST_CONFIG_PATH = PATH / 'config' / 'api.test.yml'
CONFIG_PATH = PATH / 'config' / 'api.dev.yml'

test_config = get_config(test=True, readable=True)
test_engine = create_engine(
    get_db_url(test=True)['dsn'],
    isolation_level='AUTOCOMMIT',
)
engine = create_engine(
    get_db_url(test=False)['dsn'],
    isolation_level='AUTOCOMMIT',
)


def setup_test_db(engine) -> None:
    """
    Removing the old test database environment and creating new clean
    environment.
    """
    # test params
    db_name = test_config['postgres']['database']
    db_user = test_config['postgres']['user']
    db_password = test_config['postgres']['password']

    teardown_test_db(engine)

    with engine.connect() as conn:
        conn.execute(
            f"create user {db_user} with password '{db_password}'"
        )
        conn.execute(
            f"create database {db_name} encoding 'UTF8'"
        )
        conn.execute(
            f"grant all privileges on database {db_name} to {db_user}"
        )


def teardown_test_db(engine) -> None:
    """
    Removing the test database environment.
    """
    # test params
    db_name = test_config['postgres']['database']
    db_user = test_config['postgres']['user']

    with engine.connect() as conn:
        conn.execute(
            f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid();
            """
        )
        conn.execute(f"drop database if exists {db_name}")
        conn.execute(f"drop role if exists {db_user}")


# fixtures

@pytest.yield_fixture(scope='session')
def db():
    setup_test_db(engine)
    yield
    teardown_test_db(engine)


@pytest.fixture
async def sa_engine(loop):
    return await aiopg.sa.create_engine(**test_config['postgres'])
