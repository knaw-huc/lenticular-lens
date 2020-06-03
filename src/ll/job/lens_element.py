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

    def sql(self, is_join_select):
        table = self._job.linkset_table_name(self.id) \
            if self._type == 'linkset' else self._job.lens_table_name(self.id) \
            if is_join_select else self._job.lens_view_name(self.id)
        return psycopg2_sql.Identifier(table)
