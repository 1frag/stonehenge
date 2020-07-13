import aiohttp_jinja2
import json

from aiohttp import web
from typing import Dict

from stonehenge.controllers.ctl_users import *
from stonehenge.utils.type_helper import *
from stonehenge.utils.common import get_logger

logger = get_logger(__name__)


@aiohttp_jinja2.template('index.html')
async def index(request: 'Request') -> Dict[str, str]:
    if request.user is None:
        raise web.HTTPFound('/login')

    async with request.app.db.acquire() as conn:
        data = await prepare_index_page(conn, request.user.id)
    logger.debug('%s on page /', request.user)
    return {**data, **request.to_jinja}


@aiohttp_jinja2.template('profile.html')
async def profile_view(request: 'Request'):
    if request.user is None:
        raise web.HTTPFound('/login')

    async with request.app.db.acquire() as conn:
        levels = await (
            await conn.execute('''
                select name, id=%s as current from app_levels
                order by force;
            ''', (request.user.level,))
        ).fetchall()  # todo: there something wrong: current not parsed by sqlalchemy

    return {'levels': levels, **request.to_jinja}


async def profile_save(request: 'Request'):
    if request.user is None:
        raise web.HTTPFound('/login')

    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise web.HTTPBadRequest(reason='incorrect json')

    changed = 0
    logger.debug(data)
    if 'new_level' in data:
        changed |= 1
        async with request.app.db.acquire() as conn:
            await conn.execute('''
                with cur_level as (
                    select l.id from app_levels l
                    where name=%s limit 1
                ), cur_user as (
                    select u.student_meta_id as uid from app_users u
                    where id=%s limit 1
                )
                update app_student_meta sm
                set level_id = cur_level.id
                from cur_level, cur_user
                where sm.id=cur_user.uid
            ''', (data['new_level'], request.user.id))

    logger.debug('%s fileds has been changed', changed)
    return web.Response(status=200, body=str(changed))
