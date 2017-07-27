#!/usr/bin/python

import logging
import click

from database import db, User, Role, Pdf
from flask import jsonify, g
from flask_navigation import Navigation

from raven.contrib.flask import Sentry
from flask.ext.bower import Bower
from flask_login import LoginManager
from flask_login import current_user
from flask_babel import Babel, gettext, ngettext, format_datetime, format_date
from tools.Acl import Acl

from application import create_application

app = create_application()

Bower(app)
nav = Navigation(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "user.login"
login_manager.login_message_category = "info"
app.login_manager = login_manager

if not app.debug:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

@app.before_request
def before_request():
    g.last_crawled_pdf = Pdf.query.order_by(Pdf.updated.desc()).first()
    g.last_data_update_pdf = Pdf.query.order_by(Pdf.created.desc()).first()

    menu_items = []
    menu_items.append(nav.Item('Home', 'home.get_home'))
    menu_items.append(nav.Item('API', 'api.get_doc'))
    menu_items.append(nav.Item('API Endpoint', 'api.get_blacklist'))
    if current_user.is_authenticated and Acl.validate([Role.ADMIN], current_user):
        menu_items.append(nav.Item('Users', 'user.get_user'))
        menu_items.append(nav.Item('Blacklist', 'blacklist.get_blacklist'))

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

@app.template_filter('format_date')
def format_date_filter(date_time):
    return format_date(date_time)

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
