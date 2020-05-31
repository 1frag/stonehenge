import pytest
from sqlalchemy import create_engine
import aiopg.sa


from stonehenge.utils.common import PATH, get_config
from stonehenge.app import init_app
from stonehenge.migrations import metadata
from stonehenge.users.tables import users
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


def init_sample_data(engine) -> None:
    with engine.connect() as conn:
        query = users\
            .insert()\
            .values([{
                    'id': idx,
                    'username': f'test#{idx}',
                    'email': f'test#{idx}',
                    'password': f'{idx}'} for idx in range(10)
                ])

        conn.execute(query)


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
    """
    The fixture for running and turn down database.
    """
    setup_test_db(engine)
    yield
    teardown_test_db(engine)


@pytest.yield_fixture(scope='session')
def tables(db):
    '''
    The fixture for create all tables and init simple data.
    '''
    metadata.create_all(test_engine)
    init_sample_data(test_engine)
    yield
    metadata.drop_all(test_engine)


@pytest.fixture
async def sa_engine(loop):
    '''
    The fixture initialize async engine for PostgresSQl.
    '''

    return await aiopg.sa.create_engine(**test_config['postgres'])


@pytest.fixture
async def client(aiohttp_client, tables):
    '''
    The fixture for the initialize client.
    '''
    app = init_app(['-c', TEST_CONFIG_PATH.as_posix()])

    return await aiohttp_client(app)
