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
    _local_path = PROJECT_DIR / 'static' / 'files'
    _path_on_disk = 'disk:/stonehenge/'
    _api_url = 'https://cloud-api.yandex.net:443/v1/disk/resources/upload'
    _stub_file = 'http://stonehenge-edu.herokuapp.com/static/files/readme.md'

    def __init__(self, domain):
        self._url = domain + '/static/files/'

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

    async def _create_row_in_db(
            self, name, title, href, levels,
            desc, author, conn: SAConnection
    ):
        video_id = (await (await conn.execute('''
            insert into app_video (
                cloud_path, cloud_href, title,
                description, author
            )
            values (%s, %s, %s, %s, %s)
            returning id;
        ''', (self._path_on_disk + name, href, title,
              desc, author))).fetchone())[0]
        logger.info(f'{levels=}')
        ids = await (await conn.execute('''
            insert into app_video_levels (video_id, level_id)
            select %s, id as level_id from app_levels
            where name = any (%s)
            returning id;
        ''', (video_id, levels))).fetchall()
        logger.info(f'{ids=}')
        return video_id

    async def create_new(self, title, video_file, levels, description,
                         author, conn: SAConnection):
        if not os.path.isfile(self._local_path / video_file):
            return None
        href = await self._upload_to_cloud(video_file)
        video_id = await self._create_row_in_db(
            video_file, title, href, levels, description, author, conn,
        )
        return video_id

    @staticmethod
    async def basic_view_video(vid, user_id, conn: SAConnection):
        return await (await conn.execute('''
            select id, title, cloud_href, description,
            author=%s from app_video
            where id=%s
        ''', (user_id, vid))).fetchone()

    @staticmethod
    async def edit_info(vid, title, description, user_id,
                        conn: SAConnection):
        res = await (await conn.execute('''
            with updated as (
                update app_video
                set title = %s, description = %s
                where id = %s and author = %s
                returning 1
            ) select count(*) from updated;
        ''', (title, description, vid, user_id))).fetchone()

        if not res[0]:
            # not a author or video not found
            return None, 'Video not found'
        assert res[0] == 1
        return True, 'Ok'

    @staticmethod
    async def remove(vid, user_id, conn: SAConnection):
        res = await (await conn.execute('''
            with deleted as (
                delete from app_video
                where id = %s and author = %s
                returning 1
            ) select count(*) from deleted;
        ''', (vid, user_id))).fetchone()
        if not res[0]:
            return None, 'Video not found'
        assert res[0] == 1
        return True, 'Ok'

    @staticmethod
    async def get_stats(mission, user_id, conn: SAConnection):
        if mission == 'teacher':
            return await (await conn.execute('''
                select * from app_video
                where author = %s
            ''', (user_id, ))).fetchall()
        elif mission == 'student':
            return await (await conn.execute('''
                select video.* from app_views views
                inner join app_video video on views.video_id = video.id
                where views.student=%s
            '''))
