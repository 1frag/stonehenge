import pathlib

from aiohttp import web

from stonehenge.main.views import (
    index, login_by_google, callback_by_google, login,
    registration, reg_next,
)

PROJECT_PATH = pathlib.Path(__file__).parent


def init_routes(app: web.Application) -> None:
    add_route = app.router.add_route

    add_route('*', '/', index, name='index')
    add_route('*', '/login', login, name='login')
    add_route('*', '/registration', registration, name='registration')
    add_route('*', '/reg_next', reg_next, name='reg_next')

    add_route('*', '/oauth/google', login_by_google)
    add_route('*', '/oauth/_google', callback_by_google)

    # added static dir
    static = PROJECT_PATH / 'static'
    app.router.add_static(
        '/static/', static, name='static',
    )
