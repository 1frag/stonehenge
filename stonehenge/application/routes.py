import aiohttp_session.redis_storage

from stonehenge.views.main_views import *
from utils.type_helper import *
from stonehenge.views import admin

PROJECT_PATH = pathlib.Path(__file__).parent


async def init_redis(app: 'Application'):
    await app.refresh_redis()
    app.redis_installed.set()


async def init_sessions(app: 'Application'):
    await app.redis_installed.wait()
    storage = aiohttp_session.redis_storage.RedisStorage(app.redis)
    aiohttp_session.setup(app, storage)
    app.sessions_installed.set()


def init_routes(app: 'Application') -> None:
    add_route = app.router.add_route

    add_route('POST', '/__admin__/refresh_redis', admin.refresh_redis)

    add_route('*', '/', index, name='index')
    add_route('*', '/login', login, name='login')
    add_route('*', '/registration', registration, name='registration')
    add_route('*', '/reg_next', reg_next, name='reg_next')
    add_route('*', '/sign_out', sign_out, name='sign_out')
    add_route('*', '/finish_registration', finish_registration, name='finish_registration')

    add_route('GET', '/profile', profile_view)
    add_route('POST', '/profile', profile_save)

    add_route('*', '/oauth/google', login_by_google)
    add_route('*', '/oauth/_google', callback_by_google)

    add_route('*', '/oauth/vk', login_by_vk)
    add_route('*', '/oauth/_vk', callback_by_vk)

    add_route('GET', '/tests/new', create_new_test)
    add_route('POST', '/tests/new', create_new_test)
    add_route('GET', r'/tests/{test_id:\d+}', read_test)
    add_route('GET', '/tests/exam', exam_test_get)
    add_route('POST', '/tests/exam', exam_test_post)

    # added static dir
    static = PROJECT_PATH / 'static'
    app.router.add_static(
        '/static/', static, name='static',
    )
