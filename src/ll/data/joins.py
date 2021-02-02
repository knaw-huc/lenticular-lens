from psycopg2 import sql


class Joins:
    def __init__(self):
        self._joins = []
        self._targets = []

    def add_join(self, sql, target):
        if target not in self._targets:
            self._joins.append(sql)
            self._targets.append(target)

    def set_joins_for_props(self, properties):
        for prop in properties:
            prop.add_joins(self)

    @property
    def sql(self):
        return sql.SQL('\n').join(self._joins)
