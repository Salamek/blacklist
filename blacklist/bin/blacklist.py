#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main entry-point into the 'Blacklist' Flask application.

This is a Blacklist

License: GPL-3.0
Website: https://github.com/Salamek/blacklist

Command details:
    server              Run the application using the Flask Development
                        Server. Auto-reloads files when they change.
    shell               Starts a Python interactive shell with the Flask
                        application context.
    create_all          Only create database tables if they don't exist and
                        then exit
    migrations          Migrations
    list_routes         List all available routes
    post_install        Post install script
    celerybeat          Run a Celery Beat periodic task scheduler.
    celeryworker        Run a Celery worker process.
    celerydev           Starts a Celery worker with Celery Beat in the same
                        process.
    fixtures            Generate fixtures
    configure           Configure application

Usage:
    blacklist server [-p NUM] [-l DIR] [--config_prod]
    blacklist list_routes
    blacklist shell [--config_prod]
    blacklist create_all [--config_prod]
    blacklist post_install [--config_prod]
    blacklist migrations (upgrade|current|migrate|history|heads|show|stamp|downgrade|init|revision|merge|branches|edit) [--config_prod]
    blacklist migrations stamp <revision> [--config_prod] [-h] [-d DIRECTORY] [--sql] [--tag TAG]
    blacklist celerydev [-l DIR] [--config_prod]
    blacklist celerybeat [-s FILE] [--pid=FILE] [-l DIR] [--config_prod]
    blacklist celeryworker [-n NUM] [-l DIR] [--config_prod]
    blacklist fixtures [--config_prod]
    blacklist configure [--config_prod]
    blacklist (-h | --help)

Options:
    --config_prod               Load the production configuration instead of
                                development.
    -l DIR --log_dir=DIR        Log all statements to file in this directory
                                instead of stdout.
                                Only ERROR statements will go to stdout. stderr
                                is not used.
    -n NUM --name=NUM           Celery Worker name integer.
                                [default: 1]
    --pid=FILE                  Celery Beat PID file.
                                [default: ./celery_beat.pid]
    -p NUM --port=NUM           Flask will listen on this port number.
    -s FILE --schedule=FILE     Celery Beat schedule database file.
                                [default: ./celery_beat.db]
"""

from __future__ import print_function

import hashlib
import logging
import eventlet
import logging.handlers
import os
import random
import signal
import subprocess
import sys
import urllib.parse
from functools import wraps

import flask
import yaml

from docopt import docopt
from flask_script import Shell, Manager
from flask_migrate import MigrateCommand, stamp
from celery.app.log import Logging
from celery.bin.celery import main as celery_main
from blacklist.extensions import db
from blacklist.application import create_app, get_config
from blacklist.models.blacklist import User, Role
from blacklist.config import Config
from blacklist.tools.helpers import random_password

OPTIONS = docopt(__doc__)


class CustomFormatter(logging.Formatter):
    LEVEL_MAP = {logging.FATAL: 'F', logging.ERROR: 'E', logging.WARN: 'W', logging.INFO: 'I', logging.DEBUG: 'D'}

    def format(self, record):
        record.levelletter = self.LEVEL_MAP[record.levelno]
        return super(CustomFormatter, self).format(record)


def setup_logging(name: str=None, level: int=logging.DEBUG):
    """Setup Google-Style logging for the entire application.

    At first I hated this but I had to use it for work, and now I prefer it. Who knew?
    From: https://github.com/twitter/commons/blob/master/src/python/twitter/common/log/formatters/glog.py

    Always logs DEBUG statements somewhere.

    Positional arguments:
    name -- Append this string to the log file filename.
    """
    log_to_disk = False
    if OPTIONS['--log_dir']:
        if not os.path.isdir(OPTIONS['--log_dir']):
            print('ERROR: Directory {} does not exist.'.format(OPTIONS['--log_dir']))
            sys.exit(1)
        if not os.access(OPTIONS['--log_dir'], os.W_OK):
            print('ERROR: No permissions to write to directory {}.'.format(OPTIONS['--log_dir']))
            sys.exit(1)
        log_to_disk = True

    fmt = '%(levelletter)s%(asctime)s.%(msecs).03d %(process)d %(filename)s:%(lineno)d] %(message)s'
    datefmt = '%m%d %H:%M:%S'
    formatter = CustomFormatter(fmt, datefmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR if log_to_disk else logging.DEBUG)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console_handler)

    if log_to_disk:
        file_name = os.path.join(OPTIONS['--log_dir'], 'blacklist_{}.log'.format(name))
        file_handler = logging.handlers.TimedRotatingFileHandler(file_name, when='d', backupCount=7)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def log_messages(app):
    """Log messages common to Tornado and devserver."""
    log = logging.getLogger(__name__)
    log.info('Server is running at http://{}:{}/'.format(app.config['HOST'], app.config['PORT']))
    log.info('Flask version: {}'.format(flask.__version__))
    log.info('DEBUG: {}'.format(app.config['DEBUG']))
    log.info('STATIC_FOLDER: {}'.format(app.static_folder))


def parse_options() -> Config:
    """Parses command line options for Flask.

    Returns:
    Config instance to pass into create_app().
    """
    # Figure out which class will be imported.
    if OPTIONS['--config_prod']:
        config_class_string = 'blacklist.config.Production'
    else:
        config_class_string = 'blacklist.config.Config'
    config_obj = get_config(config_class_string)

    # Force port from commandline
    if OPTIONS['--port']:
        if not OPTIONS['--port'].isdigit():
            print('ERROR: Port should be a number.')
            sys.exit(1)
        config_obj.PORT = OPTIONS['--port']

    return config_obj


def command(func):
    """Decorator that registers the chosen command/function.

    If a function is decorated with @command but that function name is not a valid "command" according to the docstring,
    a KeyError will be raised, since that's a bug in this script.

    If a user doesn't specify a valid command in their command line arguments, the above docopt(__doc__) line will print
    a short summary and call sys.exit() and stop up there.

    If a user specifies a valid command, but for some reason the developer did not register it, an AttributeError will
    raise, since it is a bug in this script.

    Finally, if a user specifies a valid command and it is registered with @command below, then that command is "chosen"
    by this decorator function, and set as the attribute `chosen`. It is then executed below in
    `if __name__ == '__main__':`.

    Doing this instead of using Flask-Script.

    Positional arguments:
    func -- the function to decorate
    """
    @wraps(func)
    def wrapped():
        return func()

    # Register chosen function.
    if func.__name__ not in OPTIONS:
        raise KeyError('Cannot register {}, not mentioned in docstring/docopt.'.format(func.__name__))
    if OPTIONS[func.__name__]:
        command.chosen = func

    return wrapped


@command
def server() -> None:
    options = parse_options()
    setup_logging('server', logging.DEBUG if options.DEBUG else logging.WARNING)
    app = create_app(options)
    log_messages(app)
    app.run(host=app.config['HOST'], port=int(app.config['PORT']), debug=app.config['DEBUG'])


@command
def shell() -> None:
    setup_logging('shell')
    app = create_app(parse_options())
    app.app_context().push()
    Shell(make_context=lambda: dict(app=app, db=db)).run(no_ipython=False, no_bpython=False)


@command
def create_all() -> None:
    setup_logging('create_all')
    app = create_app(parse_options())
    log = logging.getLogger(__name__)
    with app.app_context():
        tables_before = set(db.engine.table_names())
        db.create_all()
        tables_after = set(db.engine.table_names())
    created_tables = tables_after - tables_before
    for table in created_tables:
        log.info('Created table: {}'.format(table))


@command
def list_routes() -> None:
    output = []
    app = create_app(parse_options())
    app.config['SERVER_NAME'] = 'example.com'
    with app.app_context():
        for rule in app.url_map.iter_rules():

            integer_replaces = {}
            options = {}
            integer = 0
            for arg in rule.arguments:
                options[arg] = integer
                integer_replaces[str(integer)] = "[{0}]".format(arg)
                integer = +1

            methods = ','.join(rule.methods)
            url = flask.url_for(rule.endpoint, **options)
            for integer_replace in integer_replaces:
                url = url.replace(integer_replace, integer_replaces[integer_replace])
            line = urllib.parse.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
            output.append(line)

        for line in sorted(output):
            print(line)


@command
def post_install() -> None:
    if not os.geteuid() == 0:
        sys.exit('Script must be run as root')

    app = create_app(parse_options())
    config_path = os.path.join('/', 'etc', 'blacklist', 'config.yml')

    configuration = {}
    if os.path.isfile(config_path):
        with open(config_path) as f:
            loaded_data = yaml.load(f)
            if isinstance(loaded_data, dict):
                configuration.update(loaded_data)

    # Generate database and config if nothing is specified
    if 'SQLALCHEMY_DATABASE_URI' not in configuration or not configuration['SQLALCHEMY_DATABASE_URI']:

        configuration['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/blacklist/blacklist.db'

        # We need to set DB config to make stamp work
        app.config['SQLALCHEMY_DATABASE_URI'] = configuration['SQLALCHEMY_DATABASE_URI']

        # Create empty database
        with app.app_context():
            db.create_all()

        with app.app_context():
            stamp()

        fixtures(app)

        # Generate secret key
    if 'SECRET_KEY' not in configuration or not configuration['SECRET_KEY']:
        app.config['SECRET_KEY'] = configuration['SECRET_KEY'] = random_password()

    # Set port and host
    if 'HOST' not in configuration or not configuration['HOST']:
        configuration['HOST'] = '0.0.0.0'

    if 'PORT' not in configuration or not configuration['PORT']:
        configuration['PORT'] = 80

    # Write new configuration
    with open(config_path, 'w') as f:
        yaml.dump(configuration, f, default_flow_style=False, allow_unicode=True)


@command
def configure() -> None:
    if not os.geteuid() == 0:
        sys.exit('Script must be run as root')

    app = create_app(parse_options())
    config_path = os.path.join('/', 'etc', 'blacklist', 'config.yml')

    configuration = {}
    if os.path.isfile(config_path):
        with open(config_path) as f:
            loaded_data = yaml.load(f)
            if isinstance(loaded_data, dict):
                configuration.update(loaded_data)

    def required_input(text):
        return input(text) or required_input(text)

    def database_sqlite():
        print('SQLite configuration:')
        database_location = input('Location [/home/blacklist/blacklist.db]: ') or '/home/blacklist/blacklist.db'

        app.config['SQLALCHEMY_DATABASE_URI'] = configuration['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(database_location)

    def database_mysql():
        print('MySQL configuration:')
        database_login('mysql')

    def database_postgresql():
        print('PostgreSQL configuration:')
        database_login('postgresql')

    def database_login(database_type):
        database_server = input('Server [127.0.0.1]: ') or '127.0.0.1'
        database_name = input('Database [blacklist]: ') or 'blacklist'
        database_user = input('User [blacklist]: ') or 'blacklist'
        database_password = required_input('Password (required):')

        app.config['SQLALCHEMY_DATABASE_URI'] = configuration['SQLALCHEMY_DATABASE_URI'] = '{}://{}:{}@{}/{}'.format(
            database_type,
            database_user,
            database_password,
            database_server,
            database_name
        )

    def ignore():
        pass

    database_types = {
        0: {'name': 'Ignore', 'default': True, 'call': ignore},
        1: {'name': 'SQLite', 'default': False, 'call': database_sqlite},
        2: {'name': 'PostgreSQL', 'default': False, 'call': database_postgresql},
        3: {'name': 'MySQL', 'default': False, 'call': database_mysql},
    }

    print('Choose database type you want to use:')
    db_type_default = None
    for db_type in database_types:
        if database_types[db_type]['default']:
            db_type_default = db_type
        print('{}) {}{}'.format(
            db_type,
            database_types[db_type]['name'],
            ' (default)' if database_types[db_type]['default'] else '')
        )

    database_type = int(input('Database type [{}]: '.format(db_type_default)) or db_type_default)
    if database_type not in database_types:
        print('Invalid option selected')
        sys.exit(1)

    database_types[database_type]['call']()

    print('Webserver configuration:')
    configuration['HOST'] = input('Host [127.0.0.1]: ') or '127.0.0.1'
    configuration['PORT'] = input('Port [80]: ') or '80'

    # Write new configuration
    with open(config_path, 'w') as f:
        yaml.dump(configuration, f, default_flow_style=False, allow_unicode=True)

    print('Configuration saved.')

    recreate_database = input('Recreate database ? (y/n) [n]: ') or 'n'
    if recreate_database == 'y':
        # Create empty database
        with app.app_context():
            db.create_all()

        with app.app_context():
            stamp()

        fixtures(app)

    restart_services = input('Restart services to load new configuration ? (y/n) [n]: ') or 'n'
    if restart_services == 'y':
        subprocess.call(['systemctl', 'restart', 'blacklist_celeryworker'])
        subprocess.call(['systemctl', 'restart', 'blacklist_celerybeat'])
        subprocess.call(['systemctl', 'restart', 'blacklist'])


@command
def fixtures(app=None) -> None:
    if not app:
        options = parse_options()
        app = create_app(options)
    with app.app_context():
        roles = {
            Role.GUEST: 'Guest',
            Role.ADMIN: 'Administrator',
            Role.CUSTOMER: 'Customer',
            Role.MAINTENANCE: 'Maintenance',
        }

        for role in roles:
            found_role = Role.query.filter_by(id=role).first()
            if not found_role:
                found_role = Role()
                found_role.id = role
            found_role.name = roles[role]
            db.session.add(found_role)
            db.session.commit()

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User()
            admin.set_password('admin')
        admin.username = 'admin'
        for role in Role.query.all():
            admin.roles.append(role)

        db.session.add(admin)
        db.session.commit()


@command
def celerydev():
    setup_logging('celerydev')
    app = create_app(parse_options(), no_sql=True)
    Logging._setup = True  # Disable Celery from setting up logging, already done in setup_logging().
    celery_args = ['celery', 'worker', '-B', '-s', '/tmp/celery.db', '--concurrency=5']
    with app.app_context():
        return celery_main(celery_args)


@command
def celerybeat():
    setup_logging('celerybeat')
    app = create_app(parse_options(), no_sql=True)
    Logging._setup = True
    celery_args = ['celery', 'beat', '-C', '--pidfile', OPTIONS['--pid'], '-s', OPTIONS['--schedule']]
    with app.app_context():
        return celery_main(celery_args)


@command
def celeryworker():
    setup_logging('celeryworker{}'.format(OPTIONS['--name']))
    app = create_app(parse_options(), no_sql=True)
    Logging._setup = True
    celery_args = ['celery', 'worker', '-n', OPTIONS['--name'], '-C', '--autoscale=10,1', '--without-gossip']
    with app.app_context():
        return celery_main(celery_args)


@command
def migrations() -> None:
    app = create_app(parse_options())
    manager = Manager(app)
    manager.add_command('migrations', MigrateCommand)
    manager.run()


def main() -> None:
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))  # Properly handle Control+C
    getattr(command, 'chosen')()  # Execute the function specified by the user.


if __name__ == '__main__':
    main()

