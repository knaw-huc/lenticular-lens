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
        return psycopg2_sql.SQL('SELECT *, ARRAY[{id}] AS linksets FROM {schema}.{table}').format(
            id=psycopg2_sql.Literal(self.id),
            schema=psycopg2_sql.Identifier('linksets' if self._type == 'linkset' else 'lenses'),
            table=psycopg2_sql.Identifier(self._job.table_name(self.id))
        )
