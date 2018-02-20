# -*- coding: utf-8 -*-


from flask_babel import gettext
from wtforms import Form, validators, StringField, SubmitField


class FilterForm(Form):
    dns = StringField(None, [validators.Optional()])
    redirects_to = StringField(None, [validators.Optional()])
    a = StringField(None, [validators.Optional()])
    aaaa = StringField(None, [validators.Optional()])
    bank_account = StringField(None, [validators.Optional()])
    filter = SubmitField(label=gettext('Filter'))
    reset = SubmitField(label=gettext('Reset'))
