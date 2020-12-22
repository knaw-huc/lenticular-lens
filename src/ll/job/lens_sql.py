import locale

from psycopg2 import sql
from inspect import cleandoc
from ll.util.helpers import get_string_from_sql

locale.setlocale(locale.LC_ALL, '')


class LensSql:
    def __init__(self, job, id):
        self._job = job
        self._lens = job.get_lens_spec_by_id(id)

    def generate_lens_sql(self):
        return sql.SQL(cleandoc(
            """ DROP TABLE IF EXISTS lenses.{view_name} CASCADE;
                CREATE TABLE lenses.{view_name} AS
                {lens_sql};

                ALTER TABLE lenses.{view_name}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id text;

                ALTER TABLE lenses.{view_name} ADD COLUMN sort_order serial;

                CREATE INDEX ON lenses.{view_name} USING hash (source_uri);
                CREATE INDEX ON lenses.{view_name} USING hash (target_uri);
                CREATE INDEX ON lenses.{view_name} USING hash (cluster_id);
                CREATE INDEX ON lenses.{view_name} USING btree (sort_order);

                ANALYZE lenses.{view_name};
            """
        ) + '\n').format(
            view_name=sql.Identifier(self._job.table_name(self._lens.id)),
            lens_sql=self._lens.sql
        )

    @property
    def sql_string(self):
        return get_string_from_sql(self.generate_lens_sql())
