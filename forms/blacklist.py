from wtforms import Form, StringField, PasswordField, validators, SelectField, HiddenField, SelectMultipleField, TextAreaField, BooleanField
from database import db, Role, Blacklist
from flask_babel import Babel, gettext, ngettext

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"


class NewForm(Form):
    dns = StringField(None, [validators.Length(min=3, max=255)])
    dns_date_published = StringField(None, [validators.Length(min=1, max=60)])
    dns_date_removed = StringField(None, [validators.Length(min=1, max=60)])
    bank_account_date_published = StringField(None, [validators.Length(min=1, max=60)])
    bank_account_date_removed = StringField(None, [validators.Length(min=1, max=60)])
    bank_account = StringField(None, [validators.Length(min=1, max=60)])
    note = TextAreaField(None, [validators.Optional()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        dns_exists = Blacklist.query.filter_by(dns=self.dns.data).first()
        if dns_exists:
            self.dns.errors.append(gettext('DNS %(dns)s already exists.', dns=self.dns.data))
            return False

        return True


class EditForm(Form):
    id = HiddenField()
    dns = StringField(None, [validators.Length(min=3, max=255)])
    dns_date_published = StringField(None, [validators.Length(min=1, max=60)])
    dns_date_removed = StringField(None, [validators.Length(min=1, max=60)])
    bank_account_date_published = StringField(None, [validators.Length(min=1, max=60)])
    bank_account_date_removed = StringField(None, [validators.Length(min=1, max=60)])
    bank_account = StringField(None, [validators.Length(min=1, max=60)])
    note = TextAreaField(None, [validators.Optional()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        dns_exists = Blacklist.query.filter(Blacklist.dns == self.dns.data, Blacklist.id != self.id.data).first()
        if dns_exists:
            self.dns.errors.append(gettext('DNS %(dns)s already exists.', name=self.dns.data))
            return False

        return True