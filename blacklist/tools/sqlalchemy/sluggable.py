from itertools import chain
from slugify import slugify
from sqlalchemy import Column, Unicode, event
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound


DEFAULT_SLUG_OPTIONS = {
    'always_update': False,
    'populate_from': None,
    'separator': '-'
}


def get_class_with_tablename(cls):
    """
    Returns the first parent found (or the class itself) for given class which
    has __tablename__ attribute set.

    This function is needed for slug uniqueness testing when using concrete
    inheritance.

    :param cls: class to inspect
    """
    mapper_args = {}
    if hasattr(cls, '__mapper_args__'):
        mapper_args = cls.__mapper_args__

    if 'inherits' not in mapper_args:
        return cls
    if cls.__tablename__ != mapper_args['inherits'].__tablename__:
        return cls
    for parent in cls.__bases__:
        result = get_class_with_tablename(parent)
        if result:
            return result
    return None


class Sluggable(object):
    slug = Column(Unicode(255), unique=True, index=True, nullable=False)

    @classmethod
    def _get_slug_option(cls, name):
        try:
            return cls.__sluggable__[name]
        except (AttributeError, KeyError):
            return DEFAULT_SLUG_OPTIONS[name]

    def _update_slug(self, session):
        """
        Update the slug in this object.
        """
        populates_from = self._get_slug_option('populate_from')
        if populates_from is None:
            raise AssertionError(
                "You must specify the attribute the slug is populated from."
            )

        value = getattr(self, populates_from)
        slug = self.slugify(value)
        slug = self._ensure_slug_uniqueness(session, slug)
        self.slug = slug

    def _slug_exists(self, session, slug):
        """
        Check whether another object with the given slug already exists.

        :param session: a :class:`sqlalchemy.orm.Session` to use for querying
                        the database.
        :param slug: the slug to check for existence.
        """
        try:
            obj = session.query(
                get_class_with_tablename(self.__class__)
            ).filter_by(slug=slug).one()
            return obj is not self
        except NoResultFound:
            return False

    def _ensure_slug_uniqueness(self, session, slug):
        """
        Ensure that no other object with the given slug exists.

        The method works by appending a number to the given slug until no
        other object with such slug can be found.

        :param session: a :class:`sqlalchemy.orm.Session` to use for querying
                        the database.
        :param slug: the slug to check for existence.
        :return: a unique slug
        """
        original_slug = slug
        index = 1
        while True:
            if not self._slug_exists(session, slug):
                return slug
            index += 1
            slug = u'%(slug)s%(separator)s%(index)s' % {
                'slug': original_slug,
                'separator': self._get_slug_option('separator'),
                'index': index
            }

    def slugify(self, value):
        return slugify(value, separator=self._get_slug_option('separator'))


@event.listens_for(Session, 'before_flush')
def populate_slug(session, flush_context, instances):
    sluggables = [
        obj for obj in chain(session.new, session.dirty)
        if isinstance(obj, Sluggable)
    ]
    for sluggable in sluggables:
        always_update = sluggable._get_slug_option('always_update')
        if always_update or sluggable in session.new:
            sluggable._update_slug(session)
