import flask

from blacklist.models.blacklist import Blacklist
from blacklist.blueprints import home_index

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 30
SESSION_KEY = 'home_test_enabler'


@home_index.route('/', methods=['GET'], defaults={'page': 1})
@home_index.route('/page/<int:page>', methods=['GET'])
def get_home(page: int):
    pagination = Blacklist.query.filter().order_by(Blacklist.id.desc()).paginate(page, PER_PAGE)
    block_test_enabled = flask.session.get(SESSION_KEY, False)
    return flask.render_template('home.index.home.html', pagination=pagination, block_test_enabled=block_test_enabled)


@home_index.route('/test-enable', methods=['GET'])
def test_enable():
    flask.session[SESSION_KEY] = True
    return flask.redirect(flask.url_for('home.index.get_home'))


@home_index.route('/test-disable', methods=['GET'])
def test_disable():
    flask.session[SESSION_KEY] = False
    return flask.redirect(flask.url_for('home.index.get_home'))
