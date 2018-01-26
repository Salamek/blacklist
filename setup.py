#!/usr/bin/env python
import os
import re
import sys

from setuptools import setup, find_packages

sys_conf_dir = os.getenv("SYSCONFDIR", "/etc")

version = re.compile(r'VERSION\s*=\s*\((.*?)\)')


def get_package_version() -> str:
    base = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base, "blacklist/__init__.py")) as init_f:
        for line in init_f:
            m = version.match(line.strip())
            if not m:
                continue
            return ".".join(m.groups()[0].split(", "))


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
    Programming Language :: Python :: 2
    Programming Language :: Python :: 2.7
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
extra_files.extend(package_files('blacklist/static/layout-editor'))
extra_files.extend(package_files('blacklist/static/shape-library'))

# Bower components
extra_files.extend(package_files('blacklist/static/bower_components/bootstrap/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/bootstrap-colorpicker/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/font-awesome/css'))
extra_files.extend(package_files('blacklist/static/bower_components/font-awesome/fonts'))

extra_files.extend(package_files('blacklist/static/bower_components/jquery/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/jquery-ui'))
extra_files.extend(package_files('blacklist/static/bower_components/jquery-ui/themes/dark-hive'))

extra_files.extend(package_files('blacklist/static/bower_components/jstree/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/keyboard/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/socket.io-client/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/svg-pan-zoom/dist'))

extra_files.extend(package_files('blacklist/static/bower_components/svg.draggable.js/dist'))
extra_files.extend(package_files('blacklist/static/bower_components/svg.draw.js/dist'))
extra_files.extend(package_files('blacklist/static/bower_components/svg.js/dist'))
extra_files.extend(package_files('blacklist/static/bower_components/svg.panzoom.js/src/'))
extra_files.extend(package_files('blacklist/static/bower_components/svg.resize.js/dist'))
extra_files.extend(package_files('blacklist/static/bower_components/svg.select.js/dist'))
extra_files.extend(package_files('blacklist/static/bower_components/vis/dist'))
extra_files.extend(package_files('blacklist/static/bower_components/boostrap-menu/dist'))
extra_files.extend(package_files('blacklist/static/bower_components/select2/dist/'))

setup(
    name='blacklist',
    version=get_package_version(),
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
