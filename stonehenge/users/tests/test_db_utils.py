import pytest

from pytest import fixture

from stonehenge.users.db_utils import select_user_by_id


@pytest.mark.asyncio
async def test_select_user(tables: fixture, sa_engine: fixture) -> None:
    pass
