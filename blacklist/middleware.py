# -*- coding: utf-8 -*-

"""Flask middleware definitions. This is also where template filters are defined.

To be imported by the application.current_app() factory.
"""

import os
from logging import getLogger

from celery.signals import worker_process_init
from flask import current_app, render_template, request, g
from flask_babel import format_datetime, format_date
from blacklist.extensions import babel, db
from blacklist.models.blacklist import Pdf
from blacklist.tools.formaters import format_bytes, format_boolean
from blacklist.tools.helpers import fix_url
from markupsafe import Markup

LOG = getLogger(__name__)


# Fix Flask-SQLAlchemy and Celery incompatibilities.
@worker_process_init.connect
def celery_worker_init_db(**_) -> None:
    """Initialize SQLAlchemy right after the Celery worker process forks.
    This ensures each Celery worker has its own dedicated connection to the MySQL database. Otherwise
    one worker may close the connection while another worker is using it, raising exceptions.
    Without this, the existing session to the MySQL server is cloned to all Celery workers, so they
    all share a single session. A SQLAlchemy session is not thread/concurrency-safe, causing weird
    exceptions to be raised by workers.
    Based on http://stackoverflow.com/a/14146403/1198943
    """
    LOG.debug('Initializing SQLAlchemy for PID {}.'.format(os.getpid()))
    db.init_app(current_app)


# Setup default error templates.
@current_app.errorhandler(400)
@current_app.errorhandler(403)
@current_app.errorhandler(404)
@current_app.errorhandler(500)
def error_handler(e):
    code = getattr(e, 'code', 500)  # If 500, e == the exception.
    return render_template('{}.html'.format(code)), code


@babel.localeselector
def get_locale():
    if current_app.config['LANGUAGE']:
        return current_app.config['LANGUAGE']
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support cs/en.
    # The best match wins.
    return request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())


@babel.timezoneselector
def get_timezone():
    user = g.get('user', None)
    if user is not None:
        return user.timezone


@current_app.before_request
def before_request():
    g.last_crawled_pdf = Pdf.query.order_by(Pdf.updated.desc()).first()
    g.last_data_update_pdf = Pdf.query.order_by(Pdf.created.desc()).first()

    menu_items = [
        ('Home', 'home.index.get_home'),
        ('PDF Crawl log', 'crawl.index.get_crawl'),
        ('API', 'api.index.get_doc'),
        ('Downloads', 'download.index.get_download'),
        ('Statistics', 'statistics.index.get_statistics')
    ]

    g.menu_items = menu_items


@current_app.template_filter('format_bytes')
def format_bytes_filter(num: int) -> str:
    return format_bytes(num)


@current_app.template_filter('format_datetime')
def format_datetime_filter(date_time) -> str:
    return format_datetime(date_time)


@current_app.template_filter('format_date')
def format_date_filter(date_time) -> str:
    return format_date(date_time)


@current_app.template_filter('fix_url')
def fix_url_filter(url: str) -> str:
    return fix_url(url)


@current_app.template_filter('format_boolean')
def format_boolean_filter(bool_to_format: bool) -> Markup:
    return Markup(format_boolean(bool_to_format))


# Template filters.
@current_app.template_filter()
def whitelist(value: str) -> Markup:
    """Whitelist specific HTML tags and strings.
    Positional arguments:
    value -- the string to perform the operation on.
    Returns:
    Markup() instance, indicating the string is safe.
    """
    translations = {
        '&amp;quot;': '&quot;',
        '&amp;#39;': '&#39;',
        '&amp;lsquo;': '&lsquo;',
        '&amp;nbsp;': '&nbsp;',
        '&lt;br&gt;': '<br>',
    }
    escaped = str(Markup.escape(value))  # Escapes everything.
    for k, v in translations.items():
        escaped = escaped.replace(k, v)  # Un-escape specific elements using str.replace.
    return Markup(escaped)  # Return as 'safe'.
