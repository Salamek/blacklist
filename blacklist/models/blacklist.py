import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from blacklist.extensions import db
from blacklist.tools.sqlalchemy.uuid import GUID


__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"


class BaseTable(db.Model):
    __abstract__ = True
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    updated = db.Column(db.DateTime, default=func.now(), onupdate=func.current_timestamp())
    created = db.Column(db.DateTime, default=func.now())


blacklist_pdf_association_table = db.Table(
    'blacklist_pdf_association',
    BaseTable.metadata,
    db.Column('blacklist_id', GUID(), db.ForeignKey('blacklist.id')),
    db.Column('pdf_id', GUID(), db.ForeignKey('pdf.id'))
)


class Blacklist(BaseTable):
    __tablename__ = 'blacklist'
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.Text)


class BlacklistItem(BaseTable):
    __tablename__ = 'blacklist_item'
    dns = db.Column(db.String(255), unique=True, index=True)
    bank_account = db.Column(db.String(255), index=True)
    thumbnail = db.Column(db.Boolean)
    dns_date_published = db.Column(db.DateTime, index=True)
    dns_date_removed = db.Column(db.DateTime, index=True)
    bank_account_date_published = db.Column(db.DateTime, index=True)
    bank_account_date_removed = db.Column(db.DateTime, index=True)
    last_crawl = db.Column(db.DateTime)
    note = db.Column(db.String(255))
    redirects_to = db.Column(db.String(255), nullable=True)
    a = db.Column(db.String(255), nullable=True, index=True)
    aaaa = db.Column(db.String(255), nullable=True, index=True)

    pdfs = relationship(
        "Pdf",
        order_by="Pdf.updated.desc()",
        lazy="dynamic",
        secondary=blacklist_pdf_association_table,
        back_populates="blacklist"
    )


class BlockingLog(BaseTable):
    __tablename__ = 'blocking_log'
    blacklist_id = db.Column(db.Integer, db.ForeignKey('blacklist.id'))
    remote_addr = db.Column(db.String(255))
    tests = db.Column(db.Integer)
    success = db.Column(db.Integer)


class ApiLog(BaseTable):
    __tablename__ = 'api_log'
    remote_addr = db.Column(db.String(255))
    requests = db.Column(db.Integer)
    date = db.Column(db.Date)


class Pdf(BaseTable):
    __tablename__ = 'pdf'
    sum = db.Column(db.String(64))
    name = db.Column(db.Text)
    signed = db.Column(db.Boolean)
    ssl = db.Column(db.Boolean)
    parsed = db.Column(db.Text)
    size = db.Column(db.Integer)
    title = db.Column(db.Text)
    author = db.Column(db.Text)
    creator = db.Column(db.Text)
    format = db.Column(db.String(255))
    pages = db.Column(db.Integer)
    version = db.Column(db.Integer)

    blacklist = relationship(
        "Blacklist",
        lazy="dynamic",
        secondary=blacklist_pdf_association_table,
        back_populates="pdfs"
    )
