import re
import logging
from aiohttp import web
from aiopg.sa import SAConnection
from typing import Optional, Tuple, Dict, Union
from multidict import MultiMapping
import psycopg2
import psycopg2.errors
import json
import base64

logger = logging.getLogger(__name__)


class TestController:
    def __init__(self):
        self._reg_for_user_list = re.compile(r'a\d+')

    def _list_from_form(self, data: MultiMapping) -> list:
        result = []
        for ai in filter(self._reg_for_user_list.match, data.keys()):
            a_value = data.getone(ai)
            b_value = data.getone('b' + ai[1:], 'off') == 'on'
            result.append((a_value, b_value))
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
            if len(choice) == 0 or sum(x for _, x in choice) == 0:
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
        if choice is not None:
            choice = json.dumps(choice)

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

    async def get_next_test(self, user_id: int, conn: SAConnection):
        try:
            res = await conn.execute('''select get_next_test(%s);''', (user_id,))
            return await res.fetchone()
        except psycopg2.Error as e:
            if psycopg2.errors.lookup(e.pgcode).__name__ == 'RaiseException':
                if 'UserMustSetLevel' in e.pgerror:
                    raise UserMustSetLevel
            raise e

    @staticmethod
    def choice_to_str(choice, answer=None):
        if answer is None:
            return ' / '.join([x[0] for x in choice if x[1]])
        else:
            return ' / '.join([choice[i][0] for i in answer])

    async def check_answer(self, answer, test_id, conn: SAConnection):
        res = await (await conn.execute('''
        select type_answer, choice, correct, case_ins from app_tests where id=%s
        ''', (test_id,))).fetchone()
        if res is None:
            return None

        if res['type_answer'] == 'ch':
            choice = res['choice']
            correct = {i for i, (_, c) in enumerate(choice) if c}
            answer = set(answer)

            mark = max(+ len(correct & answer)  # правильные
                       - len(answer - correct)  # лишние
                       - len(correct - answer), 0)  # нехватающие
            return {
                'report': {
                    'correct': list(correct & answer),
                    'incorrect': list(correct.symmetric_difference(answer)),
                },
                'mark': int(100 * mark / len(correct)),
                'answer': self.choice_to_str(choice, answer),
            }
        else:
            if res['type_answer'] != 'pt' or not isinstance(answer, str):
                return None
            if res['case_ins']:
                r = answer.lower() == res['correct'].lower()
            else:
                r = answer == res['correct']
            logger.debug('%s %s %s %s', r, answer, res['correct'], res['case_ins'])
            return {
                'report': r,
                'mark': 100 if r else 0,
                'answer': answer,
            }

    async def set_mark_on_test(self, test_id, user_id, mark, answer, conn: SAConnection):
        try:
            await conn.execute('''
            insert into app_marks (solver, point, test, answer)
            values (%s, %s, %s, %s);
            ''', (user_id, mark, test_id, answer))
        except psycopg2.Error as e:
            if psycopg2.errors.lookup(e.pgcode).__name__ == 'UniqueViolation':
                raise UserAlreadyAnswerOnThisTest()

    @staticmethod
    def make_title_for_each_row(rows):
        result = []
        for row in rows:
            result.append(dict(row))
            result[-1]['title'] = row['question_txt'] or row['test']
        logger.debug('return list of %s rows {%s}', len(result), result)
        return result

    async def get_test_stat_for_teacher(self, user_id, conn: SAConnection):
        return self.make_title_for_each_row(
            await (await conn.execute('''
                select m.test, count(*), avg(m.point),
                       percentile_cont(0.5) within group (order by m.point),
                       t.*
                from app_marks m
                join app_tests t on m.test = t.id
                where author=%s
                group by m.test, t.id;
            ''', (user_id,))).fetchall())

    def precalc_test_before_show(self, test, choice_to_str=False):
        test = dict(test.items())
        if test['question_bytes']:
            test['question_bytes'] = base64.encodebytes(test['question_bytes'])
        if test['choice']:
            if choice_to_str:
                test['correct'] = self.choice_to_str(test['choice'])
            test['choice'] = enumerate(test['choice'])
        return test

    async def get_test_stat_for_student(self, user_id, conn: SAConnection):
        res = self.make_title_for_each_row(
            await (await conn.execute('''
            select t.*, m.point from app_marks m
            join app_tests t on m.test = t.id
            where m.solver=%s;
        ''', (user_id,))).fetchall())
        return res


class UserMustSetLevel(Exception):
    pass


class UserAlreadyAnswerOnThisTest(Exception):
    pass
