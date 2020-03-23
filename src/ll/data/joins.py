from psycopg2 import sql


class Joins:
    def __init__(self):
        self._joins = []
        self._targets = []

    def add_join(self, sql, target):
        if target not in self._targets:
            self._joins.append(sql)
            self._targets.append(target)

    def copy_from(self, other):
        self._joins = other.joins
        self._targets = other.targets

    @property
    def sql(self):
        return sql.SQL('\n').join(self._joins)
