import asyncio
import aiomisc
import uuid
import logging
from aiohttp import client
from multidict import MultiMapping
from aiopg.sa import SAConnection

from stonehenge.utils.constants import *

logger = logging.getLogger(__name__)


class VideoController:
    _headers = {
        'Authorization': 'OAuth ' + YANDEX_ACCESS_TOKEN,
    }
    _url = HOST + '/static/files'
    _local_path = PROJECT_DIR / 'static' / 'files'
    _path_on_disk = 'disk:/stonehenge/'
    _api_url = 'https://cloud-api.yandex.net:443/v1/disk/resources/upload'
    _stub_file = 'http://stonehenge-edu.herokuapp.com/static/files/readme.md'

    @staticmethod
    def validate(data: dict):
        if 'levels' not in data or len(data['levels']) == 0:
            return None, 'Укажите подходящие уровни знаний'
        if 'title' not in data:
            return None, 'Требуется указать название'
        if 'video_file' not in data:
            logger.debug('missed video_file field')
            return None, ''

        return {'title': data.get('title'),
                'video_file': data.get('video_file'),
                'levels': data.get('levels'),
                'description': data.get('description', '')}, None

    async def _upload_to_cloud(self, name):
        if not os.getenv('YANDEX_API_ACTIVE', False):
            return self._url + name
        opts = {
            'path': self._path_on_disk + name,
            'url': (self._url + name) if PRODUCTION else self._stub_file,
        }
        async with client.ClientSession() as session:
            async with session.post(self._api_url, params=opts,
                                    headers=self._headers) as resp:
                j = await resp.json(encoding='utf-8')
                logger.debug('json from yandex cloud: %s', j)
                return j['href']

    async def _create_row_in_db(self, name, title, href, levels, desc, conn: SAConnection):
        video_id = await (await conn.execute('''
            insert into app_video (cloud_path, cloud_href, title, description)
            values (%s, %s, %s, %s)
            returning id;
        ''', (self._path_on_disk + name, href, title, desc))).fetchone()
        await conn.execute('''
            insert into app_tests_levels (test_id, level_id)
            select %s, id as level_id from app_levels
            where name = any (%s);
        ''', (video_id, levels))
        return video_id

    async def create_new(self, title, video_file, levels, description,
                         conn: SAConnection):
        if not os.path.isfile(self._local_path / video_file):
            return None
        href = await self._upload_to_cloud(video_file)
        video_id = await self._create_row_in_db(video_file, title, href,
                                                levels, description, conn)
        # todo: должен быть механизм подчистки локального стоража,
        #  но это в будущем
        return video_id
