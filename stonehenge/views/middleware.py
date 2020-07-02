from aiohttp import web
import aiohttp_session
from typing import Callable, Awaitable
from stonehenge.controllers.ctl_users import select_user_by_id
from stonehenge.utils.type_helper import *
import logging

logger = logging.getLogger(__name__)


@web.middleware
async def identify_user(request: 'Request',
                        handler: 'Callable[[Request], Awaitable[web.Response]]'):
    session = await aiohttp_session.get_session(request)
    user_id = session.get('user_id')
    request.user = None

    if user_id is not None:  # check cookie
        async with request.app.db.acquire() as conn:  # check db
            request.user = await select_user_by_id(conn, user_id)
            if request.user is not None:
                request.to_jinja = {
                    'mission': request.user.mission,
                    'login': request.user.login,
                }

    return await handler(request)


async def init_middlewares(app: 'Application'):
    await app.sessions_installed.wait()
    app.middlewares.extend([
        identify_user,
    ])
