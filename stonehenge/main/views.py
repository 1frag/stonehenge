from typing import Dict

import aiohttp_jinja2
from aiohttp import web
import requests
import aiohttp
from typing import TYPE_CHECKING
import json
from google_auth_oauthlib.flow import Flow
from urllib.parse import urlencode
import logging

if TYPE_CHECKING:
    from stonehenge.type_helper import *

from stonehenge.users.db_utils import select_all_users
from stonehenge.type_helper import *
from stonehenge.constants import *

logging.basicConfig(
    level='DEBUG',
    format='%(levelname)s: [%(name)s at %(lineno)d] %(message)s',
)
logger = logging.getLogger('views')


@aiohttp_jinja2.template('index.html')
async def index(request: web.Request) -> Dict[str, str]:
    async with request.app['db'].acquire() as conn:
        res = await select_all_users(conn)
        res = list(res)

    return {"text": str(res)}


async def login_by_google(request: web.Request):
    opts = {
        'redirect_uri': request.app['config']['app']['domain'] + "/callback_by_google",
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


async def callback_by_google(request: web.Request):
    error = web.HTTPUnauthorized(body=b'Unauthorized, denied Google Authentication')
    if request.get('error', None):
        raise error
    opts = {
        'code': request.query.get('code'),
        'redirect_uri': 'http://localhost:8080/callback_by_google',
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'grant_type': 'authorization_code',
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                'https://oauth2.googleapis.com/token', data=opts
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
                logger.debug(await resp.text())

        async with session.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': 'Bearer ' + token_info['access_token']},
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

    return web.json_response(guser)
