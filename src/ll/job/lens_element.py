from psycopg2 import sql as psycopg2_sql


class LensElement:
    def __init__(self, data, job):
        self._id = data['id']
        self._type = data['type']
        self._job = job

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    @property
    def sql(self):
        schema = 'linksets' if self._type == 'linkset' else 'lenses'
        return psycopg2_sql.SQL('{}.{}')\
            .format(psycopg2_sql.Identifier(schema), psycopg2_sql.Identifier(self._job.table_name(self.id)))
