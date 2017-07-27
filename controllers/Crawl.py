
# -*- coding: utf-8 -*-

import flask
from database import db, Pdf

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 20

crawl = flask.Blueprint('crawl', __name__)


@crawl.route('/', methods=['GET'], defaults={'page': 1})
@crawl.route('/page/<int:page>', methods=['GET'])
def get_crawl(page):
    pagination = Pdf.query.filter().order_by(Pdf.created.desc()).paginate(page, PER_PAGE)
    return flask.render_template('crawl.html', pagination=pagination)