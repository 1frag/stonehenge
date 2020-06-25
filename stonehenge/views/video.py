import aiohttp_jinja2

from aiohttp import web

from stonehenge.controllers.ctl_users import *
from stonehenge.utils.type_helper import *
from stonehenge.controllers import *
from stonehenge.utils.common import get_logger

logger = get_logger(__name__)


@aiohttp_jinja2.template('create_new_video.html')
async def new_video_get(request: 'Request'):
    if request.user is None or request.user.mission != 'teacher':
        raise web.HTTPFound('/')
    async with request.app.db.acquire() as conn:
        levels = await get_levels(conn)
    return {'levels': enumerate(levels), **request.to_jinja}


async def new_video_post(request: 'Request'):
    clean_data, reason = request.app.video_ctrl.validate(await request.post())

    if clean_data is None:
        raise web.HTTPBadRequest(reason=reason)
    clean_data.update({'author': request.user.id})

    async with request.app.db.acquire() as conn:
        video_id = await request.app.video_ctrl.create_new(
            **clean_data, conn=conn
        )
    return web.Response(status=202, body=str(video_id))
