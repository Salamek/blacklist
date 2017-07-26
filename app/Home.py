
import flask
from database import Blacklist

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 30
home = flask.Blueprint('home', __name__)


@home.route('/', methods=['GET'], defaults={'page': 1})
@home.route('/page/<int:page>', methods=['GET'])
def get_home(page):
    pagination = Blacklist.query.filter().order_by(Blacklist.created.desc()).paginate(page, PER_PAGE)
    return flask.render_template('home.html', pagination=pagination)
