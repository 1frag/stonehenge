import asyncio
from stonehenge.utils.type_helper import *
import logging
import aiohttp.web
import aiohttp_jinja2

logger = logging.getLogger(__name__)


@aiohttp_jinja2.template('webinar_start.html')
async def start(request: 'Request'):
    if request.user is None or request.user.mission != 'teacher':
        raise aiohttp.web.HTTPFound('/')
    async with request.app.db.acquire() as conn:
        if (key := await (await conn.execute('''
            select tm.stream_key from app_teacher_meta tm
            left join app_users u on tm.id = u.teacher_meta_id
            where u.id = %s
        ''', (request.user.id, ))).fetchone()) is None:
            logger.info('key not found (user = %s)', request.user.id)
            raise aiohttp.web.HTTPFound('/')
    return {'key': key[0], **request.to_jinja}


async def current(request: 'Request'):
    if request.user is None or request.user.mission != 'teacher':
        raise aiohttp.web.HTTPFound('/')
    raise aiohttp.web.HTTPFound(f'/webinars/{request.user.id}')


@aiohttp_jinja2.template('webinar_watch.html')
async def watch(request: 'Request'):
    uid = request.match_info['w_id']
    async with request.app.db.acquire() as conn:
        c = await (await conn.execute('''
            select tm.stream_key from app_users u
            left join app_teacher_meta tm on u.teacher_meta_id = tm.id
            where u.id = %s
        ''', (uid, ))).fetchone()
        if c is None:
            raise aiohttp.web.HTTPNotFound()
    return {
        'url': f'/media/{c[0]}.m3u8',
        **request.to_jinja,
    }


async def nginx_callback(request: 'Request'):
    async with request.app.db.acquire() as conn:
        cmd = request.match_info["cmd"]
        data = await request.post()
        key = data.get('name')

        logger.info(f'new request on {cmd}')
        logger.info(await request.post())
        logger.info(request.headers.items())

        if cmd == 'publish':
            c = await (await conn.execute('''
                select count(*) from app_teacher_meta tm
                left join app_users u on tm.id = u.teacher_meta_id
                where tm.stream_key=%s
            ''', (key, ))).fetchone()
            if c[0] != 1:
                return aiohttp.web.Response(status=401)
            await conn.execute('''
                update app_teacher_meta
                set online=true
                where stream_key=%s
            ''', (key, ))
        elif cmd == 'publish_done':
            await conn.execute('''
                update app_teacher_meta
                set online=true
                where stream_key=%s
            ''', (key,))

        return aiohttp.web.Response(status=200)


@aiohttp_jinja2.template('webinar_stats.html')
async def get_all(request: 'Request'):
    if request.user is None:
        return None
    async with request.app.db.acquire() as conn:
        d = await (await conn.execute('''
            select u.* from app_users u
            inner join app_teacher_meta tm on u.teacher_meta_id = tm.id
            where tm.online;
        ''')).fetchall()
    return {'data': d}
