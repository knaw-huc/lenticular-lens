from psycopg2 import sql
from collections import OrderedDict


class Joins:
    def __init__(self):
        self._joins = OrderedDict()

    def add_join(self, sql, target):
        if target not in self._joins:
            self._joins[target] = sql

    def set_joins_for_props(self, properties):
        for prop in properties:
            prop.add_joins(self)

    def merge(self, other):
        for (target, sql) in other._joins.items():
            self._joins[target] = sql

    @property
    def sql(self):
        return sql.SQL('\n').join(list(self._joins.values()))
