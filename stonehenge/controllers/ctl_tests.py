import re
import logging
from aiohttp import web
from aiopg.sa import SAConnection
from typing import Optional, Tuple, Dict, Union
from multidict import MultiMapping

logger = logging.getLogger(__name__)


class TestController:
    def __init__(self):
        self._reg_for_user_list = re.compile(r'a\d+')

    def _list_from_form(self, data: MultiMapping) -> dict:
        result = {}
        for ai in filter(self._reg_for_user_list.match, data.keys()):
            a_value = data.getone(ai)
            b_value = data.getone('b' + ai[1:], 'off') == 'on'
            result[a_value] = b_value
        return result

    def validate(self, data: MultiMapping) -> Tuple[Optional[Dict], Optional[str]]:
        if 'question_txt' not in data and 'question_file' not in data:
            return None, 'Text of question or file should be attached'
        if ('al' not in data) or (data['al'] not in ['plain-text', 'choice']):
            return None, 'incorrect answer type'
        if data['al'] == 'plain-text' and (
                'cor-answer' not in data or
                data['cor-answer'] == ''
        ):
            return None, 'Set correct answer'
        if 'levels' not in data:
            return None, 'The test should be at least for one level'

        if data['al'] == 'choice':
            choice = self._list_from_form(data)
            if len(choice) == 0 or not any(choice.values()):
                return None, 'choice must be not empty'
            correct, case_ins = None, None
        else:
            choice = None
            correct = data.getone('cor-answer')
            case_ins = data.getone('case-ins', 'on') == 'on'

        return {'type_answer': 'ch' if data['al'] == 'choice' else 'pt',
                'correct': correct,
                'case_ins': case_ins,
                'choice': choice,
                'question_txt': data.getone('question_txt', ''),
                'question_bytes': data.getone('question_file', b''),
                'levels': data.getall('levels')}, None

    async def create_new_test(
            self, type_answer, correct, case_ins, choice,
            question_txt, question_bytes: Union[web.FileField, bytes],
            levels, author, conn: SAConnection,
    ):

        if isinstance(question_bytes, web.FileField):
            file_bytes = question_bytes.file.read()
        else:
            file_bytes = question_bytes

        test_id = (await (await conn.execute('''
            insert into app_tests (author, type_answer, correct, choice,
            question_txt, question_bytes, case_ins)
            values (%s, %s, %s, %s, %s, %s, %s)
            returning id;
        ''', (author, type_answer, correct, choice, question_txt,
              file_bytes, case_ins))).fetchone())[0]
        await (await conn.execute('''
            insert into app_tests_levels (test_id, level_id)
            select %s, id as level_id from app_levels
            where name = any (%s)
            returning id;
        ''', (test_id, levels))).fetchall()
        return test_id

    async def next_for_exam(self, user_id: int, conn: SAConnection):
        pass
