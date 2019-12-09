from psycopg2 import sql


class Joins:
    def __init__(self):
        self.joins = []
        self.targets = []

    def add_join(self, sql, target):
        if target not in self.targets:
            self.joins.append(sql)
            self.targets.append(target)

    def copy_from(self, other):
        self.joins = other.joins
        self.targets = other.targets

    @property
    def sql(self):
        return sql.SQL('\n').join(self.joins)
