import aiohttp
import aiohttp_jinja2
import certifi
import json
import ssl
import uuid

from aiohttp import web
from typing import Dict, NoReturn
from urllib.parse import urlencode

from stonehenge.controllers.ctl_users import *
from stonehenge.utils.type_helper import *
from stonehenge.utils.constants import *
from stonehenge.utils.common import get_logger

logger = get_logger(__name__)


@aiohttp_jinja2.template('login.html')
async def login(request: 'Request') -> Dict[str, str]:
    if request.user is None:
        return {}
    raise web.HTTPFound('/')


@aiohttp_jinja2.template('registration.html')
async def registration(request: 'Request') -> Dict[str, str]:
    if request.user is None:
        return {}
    raise web.HTTPFound('/')


@aiohttp_jinja2.template('reg_next.html')
async def reg_next(request: 'Request') -> Dict[str, str]:
    logger.info(request.method)
    session = await aiohttp_session.get_session(request)
    if request.user is not None:
        logger.debug(f'{request.user=}')
        raise web.HTTPFound('/')
    if session.get('way_aunt') not in ['custom', 'google', 'vk']:
        logger.debug(f'{session.get("way_aunt")=} so redirect to /registration')
        raise web.HTTPFound('/registration')
    key_pre_auth = session.get('key_pre_auth')
    try:
        saving = json.loads((await request.app.redis.get(key_pre_auth)).decode())
    except (json.JSONDecodeError, TypeError, AttributeError):
        saving = None
    logger.info(f'{saving=}')
    if saving is not None and 'auth' in saving:
        async with request.app.db.acquire() as conn:
            f, uid = (get_user_by_vk, saving.get('id_vk_user')) \
                if saving['auth'] == 'vk' else \
                (get_user_by_google, saving.get('id_g_user'))
            try:
                user = await f(conn, uid)
                logger.debug(f'{user=}')
                await remember_user(request, user)
                raise web.HTTPFound('/')
            except TypeError:
                pass
    return {
        'first_name': session.get('first_name', ''),
        'last_name': session.get('last_name', ''),
        'email': session.get('email', ''),
        'way_aunt': session['way_aunt'],
        'key_pre_auth': key_pre_auth,
    }


async def sign_out(request: 'Request'):
    session = await aiohttp_session.get_session(request)
    session.clear()
    raise web.HTTPNoContent()


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
    if way_aunt == 'google':
        id_g_user = data['id_g_user']
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
        await remember_user(request, user_id)
        raise aiohttp.web.HTTPFound('/')
    elif way_aunt == 'vk':
        id_vk_user = data['id_vk_user']
        email = session.get('email') or request.query.get('email')
        data = json.loads(await request.app.redis.get(session['key_pre_auth']))
        if data['auth'] != 'vk':
            raise aiohttp.web.HTTPBadRequest(reason='Auth method has been changed')

        async with request.app.db.acquire() as conn:
            try:
                user_id = await create_user(
                    conn, login=u_login, email=email, first_name=first_name,
                    last_name=last_name, mission=mission, vk_user=id_vk_user,
                )
            except AlreadyRegistered:
                user_id = await get_user_by_vk(conn, id_vk_user)
        await remember_user(request, user_id)
        raise aiohttp.web.HTTPFound('/')
    else:
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
        async with request.app.db.acquire() as conn:
            user_id = await get_user_by_google(conn, guser['id'])
            await remember_user(request, user_id)
    except Exception as e:
        logger.debug(f'{e.__class__}: {e}')
    else:
        raise aiohttp.web.HTTPFound('/')

    try:
        cur_uuid = uuid.uuid4().hex
        session = await aiohttp_session.get_session(request)
        session['first_name'] = guser.get('given_name', '')
        session['last_name'] = guser.get('family_name', '')
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


async def login_by_vk(request: 'Request'):
    if VK_CLIENT_ID is None:
        logger.error('VK_CLIENT_ID not set')
        raise web.HTTPServerError()

    opts = {
        'client_id': VK_CLIENT_ID,
        'redirect_uri': request.app['config']['app']['domain'] + "/oauth/_vk",
        'display': 'page',
        'scope': (1 << 16) + (1 << 22),
        'response_type': 'code',
    }
    raise web.HTTPFound('https://oauth.vk.com/authorize?' +
                        urlencode(opts))


async def callback_by_vk(request: 'Request'):
    code = request.query.get('code')
    if code is None:
        raise web.HTTPBadRequest(reason='missed auth. code')
    opts = {
        'client_id': VK_CLIENT_ID,
        'client_secret': VK_CLIENT_SECRET,
        'redirect_uri': request.app['config']['app']['domain'] + "/oauth/_vk",
        'code': code,
    }
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with aiohttp.ClientSession() as session:
        async with session.post(
                'https://oauth.vk.com/access_token', data=opts, ssl=ssl_context,
        ) as resp:  # get access token
            success = False
            try:
                data = await resp.json()
                at = data['access_token']
                user_id = data['user_id']
                email = data.get('email')
                logger.debug(await resp.json())
            except json.JSONDecodeError:
                logger.error('returned non-json format %s', await resp.text())
            except KeyError:
                logger.error('returned bad response %s', await resp.json())
            else:
                success = True
        if not success:
            raise web.HTTPBadRequest()

        async with session.get('https://api.vk.com/method/users.get', params={
            'user_id': user_id,
            'v': VK_VERSION_API,
            'access_token': at,
        }) as resp:
            try:
                data = (await resp.json())['response'][0]
            except (KeyError, IndexError, json.JSONDecodeError):
                logger.debug('non-json format %s', await resp.text())

    try:
        cur_uuid = uuid.uuid4().hex
        session = await aiohttp_session.get_session(request)
        session['first_name'] = data.get('first_name', '')
        session['last_name'] = data.get('last_name', '')
        session['email'] = email
        session['way_aunt'] = 'vk'
        session['key_pre_auth'] = cur_uuid

        save_data = {
            'auth': 'vk',
            'email': email,
            'id_vk_user': data.get('id'),
            'access_token': at,
        }
        await request.app.redis.set(cur_uuid, json.dumps(save_data))
    except Exception as e:
        logger.warning(f'{e}, {e.__class__}')

    return web.HTTPFound('/reg_next')
