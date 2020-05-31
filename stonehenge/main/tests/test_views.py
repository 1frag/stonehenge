from pytest_aiohttp import aiohttp_client


async def test_view(client: aiohttp_client) -> None:
    resp = await client.get('/')  # todo: make hinting for fixtures

    assert resp.status == 200
