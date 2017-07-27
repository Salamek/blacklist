
# -*- coding: utf-8 -*-

import flask
from database import db, Pdf, Role
from task import create_celery
from flask_login import login_user, logout_user, current_user, login_required, fresh_login_required, login_fresh
from tools.Acl import Acl

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 20

crawl = flask.Blueprint('crawl', __name__)


@crawl.route('/', methods=['GET'], defaults={'page': 1})
@crawl.route('/page/<int:page>', methods=['GET'])
def get_crawl(page):
    pagination = Pdf.query.filter().order_by(Pdf.created.desc()).paginate(page, PER_PAGE)
    return flask.render_template('crawl.html', pagination=pagination)

@login_required
@Acl.validate_path([Role.ADMIN], current_user)
@crawl.route('/trigger', methods=['GET'])
def trigger_crawl():
    celery = create_celery(flask.current_app)
    result = celery.send_task('tasks.crawl_blacklist', args=())

    return flask.jsonify({'uuid': result.id}), 200