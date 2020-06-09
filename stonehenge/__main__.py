import sys
from aiohttp import web

from stonehenge.app import init_app


def main() -> None:
    if len(sys.argv) == 1:
        raise Exception('Unknown command')
    if sys.argv[1] == 'runserver':
        app = init_app()
        app_settings = app['config']['app']
        web.run_app(
            app,
            host=app_settings['host'],
            port=app_settings['port'],
        )
    else:
        raise NotImplementedError()


main()
