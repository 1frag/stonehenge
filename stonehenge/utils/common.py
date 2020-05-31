import os
import pathlib

from aiohttp import web

PATH = pathlib.Path(__file__).parent.parent.parent


def get_db_url(test=False, readable=False):
    if os.getenv('DATABASE_URL') and not readable:
        return {
            'dsn': os.getenv('DATABASE_URL')
        }
    info = {
        'host': get_ip_from_container('stonehenge_postgres') or 'postgres',
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
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': os.getenv('PORT', 8080),
        },
        'admin_app': {
            'username': os.getenv('ADMIN_USERNAME', 'admin'),
            'password': os.getenv('ADMIN_PASSWORD', 'admin'),
        },
        'postgres': get_db_url(test, readable),
    }
    return options


def init_config(app: web.Application) -> None:
    app['config'] = get_config()


def get_ip_from_container(name):
    fmt = '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
    ip = os.popen(f"docker inspect --format='{fmt}' {name}").read()
    return ip.strip()
