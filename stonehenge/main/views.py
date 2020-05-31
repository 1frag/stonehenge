from typing import Dict

import aiohttp_jinja2
from aiohttp import web

from stonehenge.users.db_utils import select_all_users
from stonehenge.type_helper import *


@aiohttp_jinja2.template('index.html')
async def index(request: web.Request) -> Dict[str, str]:
    async with request.app['db'].acquire() as conn:
        res = await select_all_users(conn)
        res = list(res)

    return {"text": str(res)}
