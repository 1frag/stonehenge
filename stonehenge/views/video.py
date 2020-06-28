import aiohttp_jinja2
import aiohttp_session
import uuid
import base64

from aiohttp import web

from stonehenge.controllers.ctl_users import *
from stonehenge.utils.type_helper import *
from stonehenge.controllers import *
from stonehenge.utils.common import get_logger
from stonehenge.utils.constants import PROJECT_DIR

logger = get_logger(__name__)
dir_for_files = PROJECT_DIR / 'static' / 'files'


@aiohttp_jinja2.template('create_new_video.html')
async def new_video_get(request: 'Request'):
    if request.user is None or request.user.mission != 'teacher':
        raise web.HTTPFound('/')
    async with request.app.db.acquire() as conn:
        levels = await get_levels(conn)
    return {'levels': enumerate(levels), **request.to_jinja}


async def new_video_post(request: 'Request'):
    data = await request.json()
    # file data looks like 'data:application/octet-stream;base64,AAAAGG...'
    b64_data = data['file_data'].split(';')[1].split(',')[1].encode()

    session = await aiohttp_session.get_session(request)
    if data['first_time']:
        n = uuid.uuid4().hex + '.mp4'
        session['write_to_file_id'] = n
    else:
        n = session.get('write_to_file_id', None)
        if n is None:
            raise web.HTTPBadRequest()

    with open(dir_for_files / n, 'ab+') as f:
        f.write(base64.decodebytes(b64_data))

    return web.Response(status=202, body=b'Ok')

    clean_data, reason = request.app.video_ctrl.validate(
        await request.post()
    )

    if clean_data is None:
        return web.Response(status=400, body=reason)
    clean_data.update({'author': request.user.id})

    async with request.app.db.acquire() as conn:
        video_id = await request.app.video_ctrl.create_new(
            **clean_data, conn=conn
        )
    return web.Response(status=202, body=str(video_id))
