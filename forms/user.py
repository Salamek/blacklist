from wtforms import Form, StringField, PasswordField, validators, SelectField, HiddenField, SelectMultipleField
from database import db, User, Role
from flask_babel import Babel, gettext, ngettext

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

class LoginForm(Form):
    username = StringField(None, [validators.Length(min=5, max=35)])
    password = PasswordField(None, [validators.Length(min=5, max=35)])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        user = db.session.query(User).filter(User.username == self.username.data).first()
        # email and password found and match
        if user is None:
            self.username.errors.append(gettext('Username was not found.'))
            return False

        if user.check_password(self.password.data) is False:
            self.password.errors.append(gettext('Wrong password.'))
            return False

        self.user = user
        return True


class NewForm(Form):
    username = StringField(None, [validators.Length(min=5, max=35)])
    password = PasswordField(None, [validators.Length(min=5, max=35)])
    password_again = PasswordField(None, [validators.Length(min=5, max=35)])
    roles = SelectMultipleField(None, [validators.DataRequired()], choices=[], coerce=int)

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

        roles = Role.query.all()
        choices = []
        for role in roles:
            choices.append((role.id, role.name))
        self.roles.choices = choices

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        username_exists = User.query.filter_by(username=self.username.data).first()
        if username_exists:
            self.username.errors.append(gettext('Username %(username)s already exists.', username=self.username.data))
            return False

        if self.password.data != self.password_again.data:
            self.password_again.errors.append(gettext('Passwords do not match.'))
            return False

        return True


class EditForm(Form):
    id = HiddenField()
    username = StringField(None, [validators.Length(min=5, max=35)])
    password = PasswordField(None, [])
    password_again = PasswordField(None, [])
    roles = SelectMultipleField(None, [validators.DataRequired()], choices=[], coerce=int)

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

        roles = Role.query.all()
        choices = []
        for role in roles:
            choices.append((role.id, role.name))
        self.roles.choices = choices

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        username_exists = User.query.filter(User.username == self.username.data, User.id != self.id.data).first()
        if username_exists:
            self.username.errors.append(gettext('Username %(username)s already exists.', username=self.username.data))
            return False

        if self.password.data or self.password_again.data:

            if self.password.data != self.password_again.data:
                self.password_again.errors.append(gettext('Passwords do not match.'))
                return False

        return True