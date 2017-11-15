
# -*- coding: utf-8 -*-

import flask
from flask_login import login_user, logout_user, current_user, login_required, fresh_login_required, login_fresh
from forms.blacklist import EditForm, NewForm
from database import db, Role, Blacklist
from tools.Acl import Acl
from task import create_celery

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

PER_PAGE = 20

blacklist = flask.Blueprint('blacklist', __name__)


@blacklist.route('/', methods=['GET'], defaults={'page': 1})
@blacklist.route('/page/<int:page>', methods=['GET'])
@login_required
@Acl.validate_path([Role.ADMIN], current_user)
def get_blacklist(page):
    pagination = Blacklist.query.filter().order_by(Blacklist.created.desc()).paginate(page, PER_PAGE)
    return flask.render_template('blacklist.html', pagination=pagination)


@blacklist.route('/new', methods=['GET', 'POST'])
@login_required
@Acl.validate_path([Role.ADMIN], current_user)
def new_blacklist():
    form = NewForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
        blacklist_new = Blacklist()
        blacklist_new.dns = form.dns.data
        blacklist_new.dns_date_published = form.dns_date_published.data
        blacklist_new.dns_date_removed = form.dns_date_removed.data
        blacklist_new.bank_account_date_published = form.bank_account_date_published.data
        blacklist_new.bank_account_date_removed = form.bank_account_date_removed.data
        blacklist_new.bank_account = form.bank_account.data
        blacklist_new.note = form.note.data
        blacklist_new.last_crawl = None
        db.session.add(blacklist_new)
        db.session.commit()

        celery = create_celery(flask.current_app)
        celery.send_task('tasks.crawl_dns_info', args=(True,))

        flask.flash('New blacklist item was added successfully.', 'success')
        return flask.redirect(flask.url_for('blacklist.get_blacklist'))

    return flask.render_template('blacklist_new.html', form=form)


@blacklist.route('/edit/<int:blacklist_id>', methods=['GET', 'POST'])
@Acl.validate_path([Role.ADMIN], current_user)
@login_required
def edit_blacklist(blacklist_id):
    blacklist_detail = Blacklist.query.filter_by(id=blacklist_id).first_or_404()

    form = EditForm(
        flask.request.form,
        dns=blacklist_detail.dns,
        id=blacklist_detail.id,
        dns_date_published=blacklist_detail.dns_date_published,
        dns_date_removed=blacklist_detail.dns_date_removed,
        bank_account_date_published=blacklist_detail.bank_account_date_published,
        bank_account_date_removed=blacklist_detail.bank_account_date_removed,
        bank_account=blacklist_detail.bank_account,
        note=blacklist_detail.note
    )
    if flask.request.method == 'POST' and form.validate():
        blacklist_detail.dns_date_published = form.dns_date_published.data
        blacklist_detail.dns_date_removed = form.dns_date_removed.data
        blacklist_detail.bank_account_date_published = form.bank_account_date_published.data
        blacklist_detail.bank_account_date_removed = form.bank_account_date_removed.data
        blacklist_detail.bank_account = form.bank_account.data
        blacklist_detail.note = form.note.data

        if blacklist_detail.dns != form.dns.data:
            blacklist_detail.last_crawl = None

        blacklist_detail.dns = form.dns.data

        db.session.add(blacklist_detail)
        db.session.commit()
        celery = create_celery(flask.current_app)
        celery.send_task('tasks.crawl_dns_info', args=(True,))
        flask.flash('Domain was saved successfully.', 'success')
        return flask.redirect(flask.url_for('blacklist.get_blacklist'))

    return flask.render_template('blacklist_edit.html', form=form, blacklist_detail=blacklist_detail)


@blacklist.route('/delete/<int:blacklist_id>', methods=['GET'])
@login_required
@Acl.validate_path([Role.ADMIN], current_user)
def delete_blacklist(blacklist_id):
    blacklist_detail = Blacklist.query.filter_by(id=blacklist_id).first_or_404()
    db.session.delete(blacklist_detail)
    db.session.commit()
    flask.flash('Domain was deleted successfully.', 'success')

    return flask.redirect(flask.url_for('blacklist.get_domains'))