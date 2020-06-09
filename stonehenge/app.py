from pathlib import Path
from typing import (
    Optional,
    List,
    AsyncGenerator,
)

import aiohttp_jinja2
import aiopg.sa
from aiohttp import web
import jinja2
import asyncio
import aioredis

from stonehenge.routes import init_routes, init_sessions, init_redis
from stonehenge.utils.common import init_config
from stonehenge.constants import *

path = Path(__file__).parent
db_set = asyncio.Event()


def init_jinja2(app: web.Application) -> None:
    """
    Initialize jinja2 template for application.
    """
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(str(path / 'templates'))
    )


async def database(app: web.Application) -> AsyncGenerator[None, None]:
    """
    A function that, when the server is started, connects to postgresql,
    and after stopping it breaks the connection (after yield)
    """
    config = app['config']['postgres']
    print(config)
    app.db = await aiopg.sa.create_engine(**config)
    db_set.set()

    yield

    app.db.close()
    await app.db.wait_closed()


class Application(web.Application):
    redis: aioredis.commands.Redis
    db: aiopg.sa.engine.Engine
    redis_installed = asyncio.Event()


def init_app(config: Optional[List[str]] = None) -> web.Application:
    app = Application()
    init_config(app)
    init_jinja2(app)
    init_routes(app)
    app.cleanup_ctx.extend([
        database,
    ])
    app.on_startup.extend([
        init_redis,
        init_sessions,
    ])
    return app