import os
import re
import pathlib
from typing import List

from setuptools import find_packages, setup

REGEXP = re.compile(r'(\d+)\.(\d+)\.(\d+)')
ROOT = pathlib.Path(os.path.abspath(__file__)).parent


def read_version():
    pv = ROOT / '.project_version'
    with open(pv) as f:
        a, b, c = map(int, REGEXP.findall(f.read())[0])
    with open(pv, 'w') as f:
        f.write(f'{a}.{b}.{c+1}')
    return f'{a}.{b}.{c+1}'


def read_requirements(path: str) -> List[str]:
    file_path = ROOT / path
    with open(file_path) as f:
        return f.read().split('\n')


if ROOT.name in os.listdir(ROOT):
    os.chdir('..')
setup(
    name='stonehenge',
    version=read_version(),
    description='stonehenge',
    platforms=['POSIX'],
    packages=['stonehenge'],
    package_dir={'stonehenge': 'stonehenge'},
    package_data={
        '': ['config/*.*', '*static*', '*templates*']
    },
    include_package_data=True,
    install_requires=read_requirements('requirements.txt'),
    zip_safe=False,
)
