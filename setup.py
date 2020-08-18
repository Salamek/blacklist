#!/usr/bin/env python
import os
import re
import sys

from setuptools import setup, find_packages

sys_conf_dir = os.getenv("SYSCONFDIR", "/etc")


def get_requirements(filename: str) -> list:
    return open(os.path.join(filename)).read().splitlines()


def package_files(directory: str) -> list:
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

classes = """
    Development Status :: 4 - Beta
    Intended Audience :: Developers
    Programming Language :: Python
    Programming Language :: Python :: 3
    Programming Language :: Python :: 3.3
    Programming Language :: Python :: 3.4
    Programming Language :: Python :: 3.5
    Programming Language :: Python :: 3.6
    Programming Language :: Python :: Implementation :: CPython
    Programming Language :: Python :: Implementation :: PyPy
    Operating System :: OS Independent
"""
classifiers = [s.strip() for s in classes.split('\n') if s]


install_requires = get_requirements('requirements.txt')
if sys.version_info < (3, 0):
    install_requires.append('futures')


extra_files = [
        'templates/*',
        'migrations/alembic.ini',
        'views/*/templates/*',
        'views/*/templates/*/*',
        'static/*'
]

extra_files.extend(package_files('blacklist/translations'))

extra_files.extend(package_files('blacklist/static/img'))
extra_files.extend(package_files('blacklist/static/pdf'))

# Bower components
extra_files.extend(package_files('blacklist/static/bower_components/bootstrap/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/font-awesome/css'))
extra_files.extend(package_files('blacklist/static/bower_components/font-awesome/fonts'))

extra_files.extend(package_files('blacklist/static/bower_components/jquery/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/ekko-lightbox/dist'))

setup(
    name='blacklist',
    version='1.0.37',
    description='Blacklist',
    long_description=open('README.md').read(),
    author='Adam Schubert',
    author_email='adam.schubert@sg1-game.net',
    url='https://gitlab.salamek.cz/sadam/blacklist.git',
    license='GPL-3.0',
    classifiers=classifiers,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=install_requires,
    test_suite="tests",
    tests_require=install_requires,
    package_data={'blacklist': extra_files},
    entry_points={
        'console_scripts': [
            'blacklist = blacklist.__main__:main',
        ],
    },
    data_files=[
        (os.path.join(sys_conf_dir, 'systemd', 'system'), [
            'etc/systemd/system/blacklist.service',
            'etc/systemd/system/blacklist_celerybeat.service',
            'etc/systemd/system/blacklist_celeryworker.service'
        ]),
        (os.path.join(sys_conf_dir, 'blacklist'), [
            'etc/blacklist/config.yml'
        ])
    ]
)
