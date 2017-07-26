
# -*- coding: utf-8 -*-

import flask
from flask_login import login_user, logout_user, current_user, login_required, fresh_login_required, login_fresh
from forms.user import LoginForm, EditForm, NewForm
from database import User, db, Role
from tools.Acl import Acl

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 20

user = flask.Blueprint('user', __name__)


@user.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
        login_user(form.user, remember=True)
        flask.flash('Logged in successfully.', 'success')
        return flask.redirect(flask.url_for('home.get_home'))
    return flask.render_template('login.html', form=form)


@user.route('/', methods=['GET'], defaults={'page': 1})
@user.route('/page/<int:page>', methods=['GET'])
@login_required
@Acl.validate_path([Role.ADMIN], current_user)
def get_user(page):
    pagination = User.query.filter().order_by(User.created.desc()).paginate(page, PER_PAGE)
    return flask.render_template('user.html', pagination=pagination)


@user.route('/new', methods=['GET', 'POST'])
@login_required
@Acl.validate_path([Role.ADMIN], current_user)
def new_user():
    form = NewForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
        user_new = User()
        user_new.username = form.username.data
        user_new.roles = Role.query.filter(Role.id.in_(form.roles.data)).all()
        user_new.set_password(form.password.data)
        db.session.add(user_new)
        db.session.commit()
        flask.flash('New user was added successfully.', 'success')
        return flask.redirect(flask.url_for('user.get_user'))

    return flask.render_template('user_new.html', form=form)

@user.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@Acl.validate_path([Role.ADMIN], current_user)
@login_required
def edit_user(user_id):
    user_detail = User.query.filter_by(id=user_id).first_or_404()

    roles = []
    for role in user_detail.roles:
        roles.append(role.id)

    form = EditForm(flask.request.form, username=user_detail.username, id=user_detail.id, roles=roles)
    if flask.request.method == 'POST' and form.validate():
        if form.password.data:
            user_detail.set_password(form.password.data)
            flask.flash('User password has been changed.', 'success')

        user_detail.roles = Role.query.filter(Role.id.in_(form.roles.data)).all()
        user_detail.username = form.username.data
        db.session.add(user_detail)
        db.session.commit()
        flask.flash('User was saved successfully.', 'success')
        return flask.redirect(flask.url_for('user.get_user'))

    return flask.render_template('user_edit.html', form=form, user_detail=user_detail)

@user.route('/delete/<int:user_id>', methods=['GET'])
@login_required
@Acl.validate_path([Role.ADMIN], current_user)
def delete_user(user_id):
    user_detail = User.query.filter_by(id=user_id).first_or_404()
    db.session.delete(user_detail)
    db.session.commit()
    flask.flash('User was deleted successfully.', 'success')

    return flask.redirect(flask.url_for('user.get_user'))




@user.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for('user.login'))