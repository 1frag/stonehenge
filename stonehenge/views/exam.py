import aiohttp_jinja2

from aiohttp import web

from stonehenge.controllers.ctl_users import *
from stonehenge.utils.type_helper import *
from stonehenge.controllers import *
from stonehenge.utils.common import get_logger

logger = get_logger(__name__)


@aiohttp_jinja2.template('create_new_test.html')
async def create_new_test(request: 'Request'):
    if request.user and request.user.mission == 'teacher':
        if request.method == 'GET':
            async with request.app.db.acquire() as conn:
                levels = await get_levels(conn)
            return {'levels': enumerate(levels), **request.to_jinja}
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


@aiohttp_jinja2.template('read_test.html')
async def read_test(request: 'Request'):
    async with request.app.db.acquire() as conn:
        test_id = request.match_info.get('test_id')
        test = await (await conn.execute('''
        select t.*, m.point, m.answer from app_tests t
        left join app_marks m on t.id = m.test
        where t.id = %s''', (test_id,))).fetchone()

        if test is None:
            raise web.HTTPNotFound()

        test = request.app.test_ctrl.precalc_test_before_show(
            test, choice_to_str=True
        )
        return {
            'test': test,
            **request.to_jinja,
        }


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

        test = request.app.test_ctrl.precalc_test_before_show(test)
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
                data['test_id'], request.user.id, result['mark'],
                result['answer'], conn,
            )
        except UserAlreadyAnswerOnThisTest:
            raise web.HTTPBadRequest(body='choose other test')
        return web.json_response(result)


@aiohttp_jinja2.template('exam_stats.html')
async def exam_stats(request: 'Request'):
    if request.user is None:
        raise web.HTTPFound('/login')

    # потенциально сюда можно прикрутить пагинацию, но пока это не стоит
    async with request.app.db.acquire() as conn:
        if request.user.mission == 'teacher':
            res = await request.app.test_ctrl.get_test_stat_for_teacher(
                request.user.id, conn,
            )
            return {'res': res, **request.to_jinja}

        elif request.user.mission == 'student':
            res = await request.app.test_ctrl.get_test_stat_for_student(
                request.user.id, conn,
            )
            if res is None:
                raise web.HTTPNotFound()
            return {'res': res, **request.to_jinja}
