from aiohttp import web
import os
from utils.type_helper import *


async def refresh_redis(request: 'Request'):
    if request.headers.getone('Authorization') != os.getenv('ADMIN_TOKEN'):
        # In fact this response must be with status 403, but to protect
        #  brute force or something like this we will give 404.
        #  So, only, who now that there is this handler, can brute force us.
        raise web.HTTPNotFound()

    await request.app.refresh_redis()
    return web.Response(body='ok')
