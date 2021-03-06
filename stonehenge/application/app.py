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
import aiohttp.client
import aioredis

from stonehenge.application.routes import init_routes, init_sessions, init_redis
from stonehenge.utils.common import init_config
from stonehenge.views.middleware import init_middlewares
from stonehenge.controllers import TestController, VideoController
from stonehenge.utils.constants import *

path = Path(__file__).parent.parent
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
    redis: aioredis.commands.Redis = None
    db: aiopg.sa.engine.Engine
    redis_installed = asyncio.Event()
    sessions_installed = asyncio.Event()
    test_ctrl: TestController
    video_ctrl: VideoController

    def __init__(self, is_test=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_test = is_test
        init_config(self)
        self.test_ctrl = TestController()
        self.video_ctrl = VideoController(self['config']['app']['domain'])

    async def refresh_redis(self):
        try:
            if self.redis is not None:
                await self.redis.quit()
        except Exception as e:
            print(f'refreshing redis, {e.__class__}: {e}')
        self.redis = await aioredis.create_redis(self['config']['redis'])


def init_app(is_test=False) -> 'Application':
    app = Application(is_test=is_test)
    init_jinja2(app)
    init_routes(app)
    app.cleanup_ctx.extend([
        database,
    ])
    app.on_startup.extend([
        init_redis,
        init_sessions,  # after init_redis
        init_middlewares,  # after init_sessions
    ])
    return app
