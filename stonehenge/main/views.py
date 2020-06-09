from typing import Dict

import aiohttp_jinja2
from aiohttp import web
import ssl
import certifi
import aiohttp
import socket
from typing import NoReturn
import json
from urllib.parse import urlencode
import logging
import uuid
import aiohttp_session

from stonehenge.users.db_utils import (
    select_all_users, create_user, AlreadyRegistered, get_user_by_google,
)
from stonehenge.type_helper import *
from stonehenge.constants import *

logging.basicConfig(
    level='DEBUG',
    format='%(levelname)s: [%(name)s at %(lineno)d] %(message)s',
)
logger = logging.getLogger('views')


@aiohttp_jinja2.template('index.html')
async def index(request: 'Request') -> Dict[str, str]:
    async with request.app.db.acquire() as conn:
        res = await select_all_users(conn)
        res = list(res)

    return {"text": str(res)}


@aiohttp_jinja2.template('login.html')
async def login(request: 'Request') -> Dict[str, str]:
    return {}


@aiohttp_jinja2.template('registration.html')
async def registration(request: 'Request') -> Dict[str, str]:
    return {}


@aiohttp_jinja2.template('reg_next.html')
async def reg_next(request: 'Request') -> Dict[str, str]:
    logger.info(request.method)
    session = await aiohttp_session.get_session(request)
    if session.get('way_aunt') not in ['custom', 'google', 'vk']:
        logger.debug(f'{session.get("way_aunt")=} so redirect to /registration')
        raise web.HTTPFound('/registration')
    return {
        'first_name': session.get('first_name', ''),
        'last_name': session.get('last_name', ''),
        'email': session.get('email', ''),
        'way_aunt': session['way_aunt'],
        'key_pre_auth': session.get('key_pre_auth'),
    }


async def finish_registration(request: 'Request') -> NoReturn:
    session = await aiohttp_session.get_session(request)
    way_aunt = session['way_aunt']
    request_data = await request.post()
    key_pre_auth = request_data.get('key_pre_auth')
    first_name = request_data.get('first_name')
    last_name = request_data.get('last_name')
    mission = request_data.get('mission')
    u_login = request_data.get('login')
    logger.debug(f'{way_aunt=} & {key_pre_auth} & {first_name} &'
                 f'{last_name=} & {mission=} & {u_login=}')
    if key_pre_auth is None:
        raise aiohttp.web.HTTPBadRequest(reason="Key hasn't been set")
    data = json.loads(await request.app.redis.get(key_pre_auth))
    id_g_user = data['id_g_user']
    if way_aunt == 'google':
        email = session.get('email')
        data = json.loads(await request.app.redis.get(session['key_pre_auth']))
        if email != data['email']:
            raise aiohttp.web.HTTPBadRequest(reason='Email has been changed')
        if data['auth'] != 'google':
            raise aiohttp.web.HTTPBadRequest(reason='Auth method has been changed')
        async with request.app.db.acquire() as conn:
            try:
                user_id = await create_user(
                    conn, login=u_login, email=email, first_name=first_name,
                    last_name=last_name, mission=mission, google_user=id_g_user,
                )
            except AlreadyRegistered:
                user_id = await get_user_by_google(conn, id_g_user)
        session = await aiohttp_session.get_session(request)
        session['user_id'] = user_id
        raise aiohttp.web.HTTPFound('/')
    else:
        email = request.query.get('email')
        raise aiohttp.web.HTTPUnauthorized()


async def login_by_google(request: 'Request'):
    opts = {
        'redirect_uri': request.app['config']['app']['domain'] + "/oauth/_google",
        'prompt': 'consent',
        'response_type': 'code',
        'client_id': GOOGLE_CLIENT_ID,
        'scope': ' '.join([
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid',
        ]),
        'access_type': 'offline'
    }
    raise web.HTTPFound('https://accounts.google.com/o/oauth2/v2/auth?' +
                        urlencode(opts))


async def callback_by_google(request: 'Request'):
    error = web.HTTPUnauthorized(body=b'Unauthorized, denied Google Authentication')
    if request.get('error', None):
        raise error
    opts = {
        'code': request.query.get('code'),
        'redirect_uri': request.app['config']['app']['domain'] + "/oauth/_google",
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'grant_type': 'authorization_code',
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with aiohttp.ClientSession() as session:
        async with session.post(
                'https://oauth2.googleapis.com/token', data=opts, ssl=ssl_context,
        ) as resp:  # get access token
            if resp.status != 200:
                logger.info('status!=200, authorization failed %s', await resp.text())
                raise error
            try:
                token_info = await resp.json()
            except json.JSONDecodeError as e:
                logger.info('obtain non-json format %s %s', await resp.text(), e)
                raise error from None
            else:
                logger.debug(await resp.json())

        async with session.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': 'Bearer ' + token_info['access_token']},
                ssl=ssl_context,
        ) as resp:  # get profile
            try:
                guser = await resp.json()
            except aiohttp.ContentTypeError as e:
                logger.info('obtain non-json format %s %s', await resp.text(), e)
                raise error from None
            else:
                if 'error' in guser:
                    raise error
                logger.info(guser)

    try:
        cur_uuid = uuid.uuid4().hex
        session = await aiohttp_session.get_session(request)
        session['first_name'] = guser['given_name']
        session['last_name'] = guser['family_name']
        session['email'] = guser['email']
        session['way_aunt'] = 'google'
        session['key_pre_auth'] = cur_uuid

        save_data = {
            'auth': 'google',
            'email': guser['email'],
            'id_g_user': guser['id'],
            'access_token': token_info['access_token'],
        }
        await request.app.redis.set(cur_uuid, json.dumps(save_data))
    except Exception as e:
        logger.warning(f'{e}, {e.__class__}')

    return web.HTTPFound('/reg_next')
