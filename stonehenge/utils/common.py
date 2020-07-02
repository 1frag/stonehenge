import os
import pathlib
import logging

from aiohttp import web

from stonehenge.utils.constants import HOST
from stonehenge.utils.type_helper import *

PATH = pathlib.Path(__file__).parent.parent.parent
logging.basicConfig(
    level='DEBUG',
    format='%(levelname)s: [%(name)s at %(lineno)d] %(message)s',
)
logging.getLogger('parso.python.diff').disabled = True


def get_db_url(test=False, readable=False):
    if os.getenv('DATABASE_URL') and not readable:
        return {
            'dsn': os.getenv('DATABASE_URL')
        }
    info = {
        'host': 'postgres',
        'port': 5432,
        'user': 'test_user' if test else 'postgres',
        'password': 'postgres',
        'database': 'test_db' if test else 'postgres',
    }
    if readable:
        return info
    return {
        'dsn': 'postgresql://{user}:{password}@{host}:{port}/{database}'.format(**info)
    }


def get_config(test=False, readable=False):
    options = {
        'app': {
            'port': os.getenv('PORT', 8080),
            'domain': os.getenv('DOMAIN', 'http://localhost:8080'),
        },
        'admin_app': {
            'username': os.getenv('ADMIN_USERNAME', 'admin'),
            'password': os.getenv('ADMIN_PASSWORD', 'admin'),
        },
        'postgres': get_db_url(test, readable),
        'redis': os.getenv('REDIS_URL', 'redis://:redis@redis/'),
    }
    return options


def init_config(app: 'Application') -> None:
    app['config'] = get_config(test=app.is_test)


def get_logger(name):
    return logging.getLogger(name)
