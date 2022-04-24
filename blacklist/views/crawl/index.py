
# -*- coding: utf-8 -*-

import flask
from flask_login import current_user, login_required

from blacklist.models.blacklist import Pdf, Role
from blacklist.tools.Acl import Acl
from blacklist.tasks.blacklist import crawl_blacklist
from blacklist.blueprints import crawl_index

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 20


@crawl_index.route('/', methods=['GET'], defaults={'page': 1})
@crawl_index.route('/page/<int:page>', methods=['GET'])
def get_crawl(page: int):
    pagination = Pdf.query.filter().order_by(Pdf.created.desc()).paginate(page, PER_PAGE)
    return flask.render_template('crawl_index.crawl.html', pagination=pagination)


@login_required
@Acl.validate_path([Role.ADMIN], current_user)
@crawl_index.route('/trigger', methods=['GET'])
def trigger_crawl():
    result = crawl_blacklist.delay()
    flask.flash('Crawl started with UUID {}'.format(result.id), 'success')
    return flask.redirect(flask.url_for('crawl_index.get_crawl'))
