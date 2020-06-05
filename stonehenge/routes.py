import pathlib

from aiohttp import web

from stonehenge.main.views import (
    index, login_by_google, callback_by_google,
)

PROJECT_PATH = pathlib.Path(__file__).parent


def init_routes(app: web.Application) -> None:
    add_route = app.router.add_route

    add_route('*', '/', index, name='index')
    add_route('*', '/login_by_google', login_by_google)
    add_route('*', '/callback_by_google', callback_by_google)

    # added static dir
    app.router.add_static(
        '/static/',
        path=(PROJECT_PATH / 'static'),
        name='static',
    )
