import aiopg.sa
from stonehenge.utils.common import get_db_url
from typing import Awaitable

f_engine = (
    aiopg.sa
    .create_engine(get_db_url()['dsn'])
)  # type: Awaitable[aiopg.sa.f_engine.Engine]
