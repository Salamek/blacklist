#!/usr/bin/python

import flask.json
import logging
import click
import decimal

from app.Api import api
from app.Home import home
from app.User import user
from app.Blacklist import blacklist
from database import db, User, Role, Blacklist
from flask import Flask, url_for, request
from flask import jsonify
from flask_migrate import Migrate
from flask_navigation import Navigation
from dateutil.parser import parse

from raven.contrib.flask import Sentry
from flask.ext.bower import Bower
from flask_login import LoginManager
from flask_login import current_user
from flask_babel import Babel, gettext, ngettext, format_datetime
from tools.Acl import Acl

sentry = Sentry()

app = Flask(__name__)
app.config.from_object('config.Blacklist')
Bower(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "user.login"
login_manager.login_message_category = "info"
app.login_manager = login_manager
nav = Navigation(app)
babel = Babel(app)

thread = None

# sentry = Sentry(app)
# Convert decimals to floats in JSON

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

class APIoTJSONEncoder(flask.json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances to float.
            return float(obj)
        return super(APIoTJSONEncoder, self).default(obj)

app.json_encoder = APIoTJSONEncoder

db.init_app(app)
sentry.init_app(app)
app.sentry = sentry

app.register_blueprint(home)
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(blacklist, url_prefix='/blacklist')


if not app.debug:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

@app.before_request
def before_request():
    menu_items = []
    menu_items.append(nav.Item('Home', 'home.get_home'))
    if current_user.is_authenticated and Acl.validate([Role.ADMIN], current_user):
        menu_items.append(nav.Item('Users', 'user.get_user'))
        menu_items.append(nav.Item('Blacklist', 'blacklist.get_blacklist'))
        menu_items.append(nav.Item('API Endpoint', 'api.get_blacklist'))
    nav.Bar('top', menu_items)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.cli.command()
def initdb():
    with app.app_context():
        db.create_all()
        db.session.commit()
    click.echo('Init the db')

@app.cli.command()
def default_data():

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

@app.template_filter('format_datetime')
def format_datetime_filter(date_time):
    return format_datetime(date_time)

@app.template_filter('fix_url')
def fix_url_filter(url):
    if not url.startswith('http'):
        url = 'http://{}'.format(url)
    return url

@app.template_filter('format_boolean')
def format_boolean_filter(bool):
    return '<div class="label label-success">Yes</div>' if bool else '<div class="label label-danger">No</div>'

# **********
# ERRORS
# **********
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': str(error)}), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0')
