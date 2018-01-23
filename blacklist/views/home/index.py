import flask

from blacklist.models.blacklist import Blacklist
from blacklist.blueprints import home_index

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 30


@home_index.route('/', methods=['GET'], defaults={'page': 1})
@home_index.route('/page/<int:page>', methods=['GET'])
def get_home(page):
    pagination = Blacklist.query.filter().order_by(Blacklist.id.desc()).paginate(page, PER_PAGE)
    return flask.render_template('home.index.home.html', pagination=pagination)
