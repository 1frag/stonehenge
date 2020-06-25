import asyncio
import aiomisc
import uuid
from aiohttp import client
from multidict import MultiMapping
from aiopg.sa import SAConnection

from stonehenge.utils.constants import *


class VideoController:
    _headers = {
        'Authorization': 'OAuth ' + YANDEX_ACCESS_TOKEN,
    }
    _url = HOST + '/static/files'
    _local_path = PROJECT_DIR / 'static' / 'files'
    _path_on_disk = 'disk:/stonehenge/'
    _api_url = 'https://cloud-api.yandex.net:443/v1/disk/resources/upload'

    @staticmethod
    def validate(data: MultiMapping):
        if 'video_file' not in data:
            return None, 'Файл с видео должен быть прикреплен'
        if 'levels' not in data or len(data.getall('levels')) == 0:
            return None, 'Укажите подходящие уровни знаний'
        if 'title' not in data:
            return None, 'Требуется указать название'

        return {'title': data.getone('title'),
                'video_file': data.getone('question_file'),
                'levels': data.getall('levels'),
                'description': data.getone('description', '')}, None

    @aiomisc.threaded
    def save_on_localhost(self, bytes_to_save):
        name = f'{uuid.uuid4().hex}.mp4'
        with open(name, 'wb') as f:
            f.write(bytes_to_save)
        return name

    async def upload_to_cloud(self, name):
        opts = {
            'path': self._path_on_disk + name,
            'url': self._url + name,
        }
        async with client.ClientSession() as session:
            async with session.post(self._api_url, params=opts,
                                    headers=self._headers) as resp:
                return (await resp.json())['href']

    async def create_row_in_db(self, name, title, href, levels, desc, conn: SAConnection):
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
        name = await self.save_on_localhost(video_file)
        href = await self.upload_to_cloud(name)
        video_id = await self.create_row_in_db(name, title, href, levels,
                                               description, conn)
        # todo: должен быть механизм подчистки локального стоража,
        #  но это в будущем
        return video_id
