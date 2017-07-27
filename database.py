from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import sys
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

class BaseTable(db.Model):
    __abstract__ = True
    updated = db.Column(db.DateTime, default=func.now(), onupdate=func.current_timestamp())
    created = db.Column(db.DateTime, default=func.now())

user_role_association_table = db.Table('user_role_association', BaseTable.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)


class User(BaseTable):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    roles = relationship(
        "Role",
        secondary=user_role_association_table,
        back_populates="users")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_active(self):
        return True

    #@property
    def is_authenticated(self):
        return True

    #@property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            if isinstance(self.id, str):
                return self.id
            elif isinstance(self.id, int):
                return self.id
            else:
                return self.id
        except AttributeError:
            raise NotImplementedError('No `id` attribute - override `get_id`')

    def __eq__(self, other):
        """
        Checks the equality of two `UserMixin` objects using `get_id`.
        """
        if isinstance(other, User):
            return self.get_id() == other.get_id()
        return NotImplemented

    def __ne__(self, other):
        """
        Checks the inequality of two `UserMixin` objects using `get_id`.
        """
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal
    if sys.version_info[0] != 2:  # pragma: no cover
        # Python 3 implicitly set __hash__ to None if we override __eq__
        # We set it back to its default implementation
        __hash__ = object.__hash__

class Role(BaseTable):
    GUEST = 1
    ADMIN = 2
    CUSTOMER = 3
    MAINTENANCE = 4

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    users = relationship(
        "User",
        secondary=user_role_association_table,
        back_populates="roles")

    def __repr__(self):
        return self.name

class Blacklist(BaseTable):
    __tablename__ = 'blacklist'
    id = db.Column(db.Integer, primary_key=True)
    dns = db.Column(db.String(255), unique=True)
    bank_account = db.Column(db.String(255))
    thumbnail = db.Column(db.Boolean)
    signed = db.Column(db.Boolean)
    ssl = db.Column(db.Boolean)
    date = db.Column(db.DateTime)
    note = db.Column(db.String(255))

class BlockingLog(BaseTable):
    __tablename__ = 'blocking_log'
    id = db.Column(db.Integer, primary_key=True)
    blacklist_id = db.Column(db.Integer, db.ForeignKey('blacklist.id'))
    remote_addr = db.Column(db.String(255))
    tests = db.Column(db.Integer)
    success = db.Column(db.Integer)

class ApiLog(BaseTable):
    __tablename__ = 'api_log'
    id = db.Column(db.Integer, primary_key=True)
    remote_addr = db.Column(db.String(255))
    requests = db.Column(db.Integer)