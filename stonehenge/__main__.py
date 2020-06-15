import asyncio
import sys
from aiohttp import web

from stonehenge.app import init_app, database


def main() -> None:
    if len(sys.argv) == 1:
        raise Exception('Unknown command')

    app = init_app()
    app_settings = app['config']['app']

    if sys.argv[1] == 'runserver':
        web.run_app(
            app,
            host=app_settings['host'],
            port=app_settings['port'],
        )

    elif sys.argv[1] == 'migrate':
        with open('/app/db_state/migrate.sql') as f:
            sql = f.read()

        async def async_func():
            db_state = database(app)
            await db_state.__anext__()
            async with app.db.acquire() as conn:
                await conn.execute(sql)
            try:
                await db_state.__anext__()
            except (StopAsyncIteration, StopIteration):
                pass

        asyncio.run(async_func())
        print('done')
    else:
        raise NotImplementedError()


main()
