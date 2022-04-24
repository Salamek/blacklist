
# -*- coding: utf-8 -*-

import flask
from flask_login import login_user, logout_user, login_required

from blacklist.blueprints import sign_index
from blacklist.forms.sign import InForm


__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 20


@sign_index.route('/in', methods=['GET', 'POST'])
def login():
    form = InForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
        login_user(form.user, remember=True)
        flask.flash('Logged in successfully.', 'success')
        return flask.redirect(flask.url_for('home_index.get_home'))
    return flask.render_template('sign.index.login.html', form=form)


@sign_index.route("/out")
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for('sign_index.login'))
