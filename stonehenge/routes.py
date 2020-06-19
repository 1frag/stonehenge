import pathlib
import os

from aiohttp import web
import aioredis

import aiohttp_session
import aiohttp_session.redis_storage
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from stonehenge.main.views import *
from stonehenge.type_helper import *

PROJECT_PATH = pathlib.Path(__file__).parent


async def init_redis(app: 'Application'):
    app.redis = await aioredis.create_redis(app['config']['redis'])
    app.redis_installed.set()


async def init_sessions(app: 'Application'):
    await app.redis_installed.wait()
    storage = aiohttp_session.redis_storage.RedisStorage(app.redis)
    aiohttp_session.setup(app, storage)
    app.sessions_installed.set()


def init_routes(app: 'Application') -> None:
    add_route = app.router.add_route

    add_route('*', '/', index, name='index')
    add_route('*', '/login', login, name='login')
    add_route('*', '/registration', registration, name='registration')
    add_route('*', '/reg_next', reg_next, name='reg_next')
    add_route('*', '/finish_registration', finish_registration, name='finish_registration')

    add_route('*', '/oauth/google', login_by_google)
    add_route('*', '/oauth/_google', callback_by_google)

    add_route('*', '/oauth/vk', login_by_vk)
    add_route('*', '/oauth/_vk', callback_by_vk)

    add_route('GET', '/tests/new', create_new_test)
    add_route('POST', '/tests/new', create_new_test)
    add_route('GET', r'/tests/{test_id:\d+}', read_test)
    add_route('GET', r'/tests/exam', exam_test)

    # added static dir
    static = PROJECT_PATH / 'static'
    app.router.add_static(
        '/static/', static, name='static',
    )
