import pytest

from pytest import fixture


@pytest.mark.asyncio
async def test_select_user(tables: fixture, sa_engine: fixture) -> None:
    pass
