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
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
from aiohttp_oauth2.client.contrib import google

from stonehenge.routes import init_routes
from stonehenge.utils.common import init_config
from stonehenge.users.tables import users
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
    engine = await aiopg.sa.create_engine(**config)
    app['db'] = engine
    db_set.set()

    yield

    app['db'].close()
    await app['db'].wait_closed()


def init_app(config: Optional[List[str]] = None) -> web.Application:
    app = web.Application()
    init_config(app)
    init_jinja2(app)
    init_routes(app)
    app.cleanup_ctx.extend([
        database,
    ])
    return app
