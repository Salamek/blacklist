
# -*- coding: utf-8 -*-

import flask
from blacklist.models.blacklist import Pdf
from blacklist.blueprints import crawl_index

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 20


@crawl_index.route('/', methods=['GET'], defaults={'page': 1})
@crawl_index.route('/page/<int:page>', methods=['GET'])
def get_crawl(page: int):
    pagination = Pdf.query.filter().order_by(Pdf.created.desc()).paginate(page, PER_PAGE)
    return flask.render_template('crawl_index.crawl.html', pagination=pagination)
