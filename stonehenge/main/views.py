from typing import Dict

import aiohttp_jinja2
from aiohttp import web
import ssl
import certifi
import aiohttp
from typing import NoReturn
import json
from urllib.parse import urlencode
import uuid
import base64

from stonehenge.users.db_utils import *
from stonehenge.type_helper import *
from stonehenge.constants import *
from stonehenge.controllers import *

logging.basicConfig(
    level='DEBUG',
    format='%(levelname)s: [%(name)s at %(lineno)d] %(message)s',
)
logging.getLogger('parso.python.diff').disabled = True
logger = logging.getLogger('views')


@aiohttp_jinja2.template('index.html')
async def index(request: 'Request') -> Dict[str, str]:
    if request.user is None:
        raise web.HTTPFound('/login')

    async with request.app.db.acquire() as conn:
        data = {'login': request.user.login,
                'mission': request.user.mission}
        if request.user.mission == 'teacher':
            data.update(await prepare_index_page_for_teacher(conn, request.user.id))
    return data


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
                await remember_user(request, await f(conn, uid))
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


@aiohttp_jinja2.template('profile.html')
async def profile_view(request: 'Request'):
    if request.user is None:
        raise web.HTTPFound('/login')

    async with request.app.db.acquire() as conn:
        levels = await (
            await conn.execute('''
            select name, id=%s as current from app_levels order by force;
            ''', (request.user.level, ))
        ).fetchall()  # todo: there something wrong: current not parsed by sqlalchemy

    return {'mission': request.user.mission,
            'levels': levels}


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


@aiohttp_jinja2.template('create_new_test.html')
async def create_new_test(request: 'Request'):
    if request.user and request.user.mission == 'teacher':
        if request.method == 'GET':
            async with request.app.db.acquire() as conn:
                levels = await get_levels(conn)
            return {'levels': enumerate(levels)}
        elif request.method == 'POST':
            clean_data, reason = request.app.test_ctrl.validate(await request.post())
            if clean_data is None:
                raise web.HTTPBadRequest(reason=reason)
            clean_data.update({'author': request.user.id})
            async with request.app.db.acquire() as conn:
                test_id = await request.app.test_ctrl.create_new_test(**clean_data, conn=conn)

            # ajax skips 302, and even the statusCode field doesn't prevent
            # redirection, so I need to do a bad practice, and now I'm
            # sending 202 instead of 302, the client side should open another
            # page: / tests / {test_id}, where the test_id will be passed in
            # the body. This code is not recommended from the RFC, but we
            # probably need to use the net-ajax method to connect to the server,
            return web.Response(status=202, body=f'{test_id}')  # so it's hard now

    logger.info('unsuccessful result on page create_new_test by '
                f'{request.user=}')
    raise web.HTTPFound('/')


async def read_test(request: 'Request'):
    async with request.app.db.acquire() as conn:
        test_id = request.match_info.get('test_id')
        res = await conn.execute('''
        select * from app_tests
        where id = %s''', (test_id,))

        if one := await res.fetchone():
            return web.Response(body=str(dict(one.items())))
        raise web.json_response({
            'error': '???',
            'test_id': test_id,
        })


@aiohttp_jinja2.template('exam_test.html')
async def exam_test_get(request: 'Request'):
    if request.user is None or request.user.mission != 'student':
        logger.info(f'{request.user=} tried exam))')
        raise web.HTTPFound('/')

    async with request.app.db.acquire() as conn:
        try:
            data = await request.app.test_ctrl.get_next_test(
                request.user.id, conn
            )
        except UserMustSetLevel:
            # todo: future task will create page /profile
            #  and there we catch this flag to show error
            raise web.HTTPFound('/profile?set_up_level')
        if data is None:
            return aiohttp_jinja2.render_template(
                'error.html', request, {'error': 'there is no tests'}
            )
        test = await (await conn.execute('''
        select * from app_tests
        where id = %s''', data)).fetchone()
        if test is None:
            raise web.HTTPFound('/?no-more-tests')
        test = dict(test.items())
        if test['question_bytes']:
            test['question_bytes'] = base64.encodebytes(test['question_bytes'])
        if test['choice']:
            test['choice'] = enumerate(test['choice'])
        return {'test': test}


async def exam_test_post(request: 'Request'):
    if request.user is None or request.user.mission != 'student':
        raise web.HTTPForbidden()

    data: dict = await request.json()
    if not all(map(data.__contains__, ('answer', 'test_id'))):
        raise web.HTTPBadRequest()

    async with request.app.db.acquire() as conn:
        res = await (await conn.execute('''
        select test_suitable_for_student(%s, %s)
        ''', (request.user.id, data['test_id']))).fetchone()
        if not res:
            raise web.HTTPForbidden()

        result = await request.app.test_ctrl.check_answer(
            data['answer'], data['test_id'], conn
        )
        if result is None:
            raise web.HTTPBadRequest()
        try:
            await request.app.test_ctrl.set_mark_on_test(
                data['test_id'], request.user.id, result['mark'], conn,
            )
        except UserAlreadyAnswerOnThisTest:
            raise web.HTTPBadRequest(body='choose other test')
        return web.json_response(result)
