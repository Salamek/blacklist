import flask

from blacklist.models.blacklist import Blacklist
from blacklist.blueprints import home_index
from blacklist.forms.home import FilterForm

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 30
SESSION_KEY = 'home_test_enabler'
SESSION_KEY_FILTER = 'home_filter'


@home_index.route('/', methods=['GET', 'POST'], defaults={'page': 1})
@home_index.route('/page/<int:page>', methods=['GET'])
def get_home(page: int):
    default_data = {
        'dns': '',
        'redirects_to': '',
        'a': '',
        'aaaa': '',
        'bank_account': '',
        'filtered': False
    }

    form_data = flask.session.get(SESSION_KEY_FILTER, default_data).copy()

    form = FilterForm(
        flask.request.form,
        dns=form_data['dns'],
        redirects_to=form_data['redirects_to'],
        a=form_data['a'],
        aaaa=form_data['aaaa'],
        bank_account=form_data['bank_account']
    )

    if flask.request.method == 'POST' and form.validate():
        if form.filter.data:
            form_data = form.data
            form_data['filtered'] = True
            form_data_save = form_data

            flask.session[SESSION_KEY_FILTER] = form_data_save
        else:
            flask.session.pop(SESSION_KEY_FILTER, None)
            return flask.redirect(flask.url_for('home.index.get_home'))

    blacklist_filter = []
    if form_data['dns'] != default_data['dns']:
        blacklist_filter.append(Blacklist.dns.like("%{}%".format(form_data['dns'])))

    if form_data['redirects_to'] != default_data['redirects_to']:
        blacklist_filter.append(Blacklist.redirects_to.like("%{}%".format(form_data['redirects_to'])))

    if form_data['a'] != default_data['a']:
        blacklist_filter.append(Blacklist.a.like("%{}%".format(form_data['a'])))

    if form_data['aaaa'] != default_data['aaaa']:
        blacklist_filter.append(Blacklist.aaaa.like("%{}%".format(form_data['aaaa'])))

    if form_data['bank_account'] != default_data['bank_account']:
        blacklist_filter.append(Blacklist.bank_account.like("%{}%".format(form_data['bank_account'])))

    pagination = Blacklist.query.filter(*blacklist_filter).order_by(Blacklist.id.desc()).paginate(page, PER_PAGE)
    block_test_enabled = flask.session.get(SESSION_KEY, False)
    return flask.render_template(
        'home.index.home.html',
        pagination=pagination,
        block_test_enabled=block_test_enabled,
        form=form,
        filtered=form_data['filtered']
    )


@home_index.route('/test-enable', methods=['GET'])
def test_enable():
    flask.session[SESSION_KEY] = True
    return flask.redirect(flask.url_for('home.index.get_home'))


@home_index.route('/test-disable', methods=['GET'])
def test_disable():
    flask.session[SESSION_KEY] = False
    return flask.redirect(flask.url_for('home.index.get_home'))
