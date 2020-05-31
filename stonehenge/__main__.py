import os
import sys
import json
import re
from aiohttp import web
from subprocess import Popen

from stonehenge.app import init_app

python = f'{sys.prefix}/bin/python'


def path_from_root(*args: str) -> str:
    return os.path.join(
        os.path.dirname(__file__), *args
    )


def create_app() -> web.Application:
    import aiohttp_debugtoolbar

    app = init_app()
    aiohttp_debugtoolbar.setup(app, check_host=False)

    return app


def main() -> None:
    path_to_setup_py = path_from_root('../setup.py')
    # os.popen(f'{python} {path_to_setup_py} install').read()
    if len(sys.argv) == 1:
        raise Exception('Unknown command')
    if sys.argv[1] == 'runserver':
        app = init_app()
        app_settings = app['config']['app']
        web.run_app(
            app,
            host=app_settings['host'],
            port=app_settings['port'],
        )
    elif sys.argv[1] == 'migrate':
        if len(sys.argv) < 2:
            raise Exception('Second argument has missed')

        path_env_json = path_from_root('migrations/env.json')
        versions_dir = path_from_root('migrations/versions')

        tv = int(sys.argv[2])
        with open(path_env_json) as f:
            config = json.load(f)
        cv = config['current_version']
        direct = (-1, 'downgrade') if (cv > tv) else (1, 'upgrade')
        print(f'{cv=}; {tv=}')

        do = range(min(cv, tv) + 1, max(cv, tv) + 1)[::direct[0]]
        migration_template = re.compile(r'\d{4}_\w+\.py')
        mapping = {
            int(s[:4]): s
            for s in os.listdir(versions_dir)
            if migration_template.match(s)
        }
        failed = False
        for i in do:
            cmd = [python, f'{versions_dir}/{mapping[i]}', direct[1]]
            proc = Popen(cmd)
            proc.communicate()
            if proc.returncode != 0:
                failed = True
            print(i, direct[1])

        if not failed:
            config['current_version'] = tv
            with open(path_env_json, 'w') as f:
                json.dump(config, f, indent=4)


main()
