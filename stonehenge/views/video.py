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
    n = uuid.uuid4().hex + '.mp4'
    with open(dir_for_files / n, 'w') as f:
        f.write('')  # now we just create this file

    await request.app.redis.set('author_' + n, request.user.id)
    logger.debug('redis: add(%s, %s)', 'author_' + n, request.user.id)
    return web.Response(status=201, body=n)


async def new_video_upload(request: 'Request'):
    data = await request.json()
    if 'file_data' not in data or 'n' not in data:
        raise web.HTTPBadRequest()

    author = await request.app.redis.get('author_' + data['n'])
    logger.debug('redis: get(%s, %s)', 'author_' + data['n'], author)
    if author != str(request.user.id).encode():
        logger.info('forbidden access to %s from %s',
                    data['n'], request.user.id)
        raise web.HTTPForbidden()

    try:
        # file data looks like 'data:application/octet-stream;base64,AAAAGG...'
        b64_data = data['file_data'].split(';')[1].split(',')[1].encode()
    except (KeyError, IndexError, TypeError):
        logger.error('Unexpected data format %s', data['file_data'])
        raise web.HTTPBadRequest()

    with open(dir_for_files / data['n'], 'ab+') as f:
        f.write(base64.decodebytes(b64_data))

    return web.Response(status=202, body=b'Ok')


async def new_video_updated(request: 'Request'):
    data = await request.json()
    resp, err = request.app.video_ctrl.validate(data)
    if resp is None:
        raise web.HTTPBadRequest(body=err)
    async with request.app.db.acquire() as conn:
        video_id = await request.app.video_ctrl.create_new(
            **resp, author=request.user.id, conn=conn,
        )
    return web.Response(status=202, body=str(video_id))


@aiohttp_jinja2.template('read_video.html')
async def read_video(request: 'Request'):
    if request.user is None or request.user.mission == 'advertiser':
        raise web.HTTPFound('/')

    vid = request.match_info['video_id']
    async with request.app.db.acquire() as conn:
        video = await request.app.video_ctrl.basic_view_video(
            vid, request.user.id, conn=conn,
        )
        if video is None:
            raise web.HTTPNotFound()
    return {'video': video, **request.to_jinja}


async def edit_video_info(request: 'Request'):
    if request.user is None:
        raise web.HTTPForbidden()
    data = await request.post()
    if not all(map(data.__contains__,
                   ('title', 'description', 'v_id'))):
        raise web.HTTPBadRequest()

    async with request.app.db.acquire() as conn:
        res, err = await request.app.video_ctrl.edit_info(
            data['v_id'], data['title'], data['description'],
            request.user.id, conn,
        )
        if res is None:
            raise web.HTTPBadRequest(body=err)
    return web.Response(status=200)


async def remove_video(request: 'Request'):
    if request.user is None:
        raise web.HTTPForbidden()
    data = await request.json()
    if 'v_id' not in data:
        raise web.HTTPBadRequest()

    async with request.app.db.acquire() as conn:
        res, err = await request.app.video_ctrl.remove(
            data['v_id'], request.user.id, conn,
        )
        if res is None:
            raise web.HTTPNotFound(body=err)
    return web.Response(status=200)
