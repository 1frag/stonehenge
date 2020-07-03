import aiohttp_session.redis_storage
import pathlib

from stonehenge import views
from stonehenge.utils.type_helper import *

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

    add_route('POST', '/__admin__/refresh_redis', views.admin.refresh_redis)

    add_route('*', '/', views.basic.index)
    add_route('GET', '/profile', views.basic.profile_view)
    add_route('POST', '/profile', views.basic.profile_save)

    add_route('*', '/login', views.auth.login)
    add_route('*', '/registration', views.auth.registration)
    add_route('*', '/reg_next', views.auth.reg_next)
    add_route('*', '/sign_out', views.auth.sign_out)
    add_route('*', '/finish_registration', views.auth.finish_registration)

    add_route('*', '/oauth/google', views.auth.login_by_google)
    add_route('*', '/oauth/_google', views.auth.callback_by_google)

    add_route('*', '/oauth/vk', views.auth.login_by_vk)
    add_route('*', '/oauth/_vk', views.auth.callback_by_vk)

    add_route('GET', '/tests/new', views.exam.create_new_test)
    add_route('POST', '/tests/new', views.exam.create_new_test)
    add_route('GET', r'/tests/{test_id:\d+}', views.exam.read_test)
    add_route('GET', '/tests/exam', views.exam.exam_test_get)
    add_route('POST', '/tests/exam', views.exam.exam_test_post)
    add_route('GET', '/tests/stats', views.exam.exam_stats)

    add_route('GET', '/video/new', views.video.new_video_get)
    add_route('POST', '/video/new', views.video.new_video_post)
    add_route('POST', '/video/upload', views.video.new_video_upload)
    add_route('POST', '/video/updated', views.video.new_video_updated)
    add_route('GET', r'/video/{video_id:\d+}', views.video.read_video)
    add_route('POST', '/video/edit', views.video.edit_video_info)

    # added static dir
    static = PROJECT_PATH / '..' / 'static'
    app.router.add_static(
        '/static/', static, name='static',
    )
