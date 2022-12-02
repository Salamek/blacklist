import hashlib
import pickle
import typing
from itertools import chain
from sqlalchemy import Column, Unicode, event
from sqlalchemy.orm import Session


DEFAULT_UNIQUE_NULL_OPTIONS = {
    'always_update': True,
    'populate_from': None,
}


class UniqueNull:
    unique_null = Column(Unicode(64), unique=True, index=True, nullable=False)

    @classmethod
    def get_unique_null_option(cls, name):
        try:
            return cls.__unique_null__[name]
        except (AttributeError, KeyError):
            return DEFAULT_UNIQUE_NULL_OPTIONS[name]

    def update_unique_null(self):
        """
        Update the unique_null in this object.
        """
        populates_from = typing.cast(typing.List[str], self.get_unique_null_option('populate_from'))
        if populates_from is None:
            raise AssertionError(
                "You must specify the attribute the unique_null is populated from."
            )

        populates_from.sort()
        values = self._resolve_values(populates_from)
        self.unique_null = self._generate_sum(values)

    def _resolve_values(self, populate_from: typing.List[str]):
        values = []
        for populate_from_col in populate_from:
            if '.' in populate_from_col:
                dot_parts = populate_from_col.split('.')
                resolved_value = None
                for dot_part in dot_parts:
                    if not resolved_value:
                        resolved_value = getattr(self, dot_part)
                    else:
                        resolved_value = getattr(resolved_value, dot_part)
                values.append(resolved_value)
            else:
                values.append(getattr(self, populate_from_col))

        return values

    def _generate_sum(self, values: list):
        sha256_hash = hashlib.sha256()
        for value in values:
            pickled_value = pickle.dumps(value)
            sha256_hash.update(pickled_value)
        return sha256_hash.hexdigest()


@event.listens_for(Session, 'before_flush')
def populate_unique_null(session, flush_context, instances):
    unique_nullables = [
        obj for obj in chain(session.new, session.dirty)
        if isinstance(obj, UniqueNull)
    ]
    for unique_nullable in unique_nullables:
        always_update = unique_nullable.get_unique_null_option('always_update')
        if always_update or unique_nullable in session.new:
            unique_nullable.update_unique_null()
