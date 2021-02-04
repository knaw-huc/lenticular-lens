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
        if self._lens.similarity_fields and self._lens.similarity_threshold_sqls:
            sim_fields_sql = [sql.SQL('{} numeric[]').format(sql.Identifier(sim_field))
                              for sim_field in self._lens.similarity_fields]

            return sql.SQL(cleandoc(
                """ DROP TABLE IF EXISTS lenses.{lens} CASCADE;
                    CREATE TABLE lenses.{lens} AS
                    SELECT lens.*
                    FROM (
                        {lens_sql}
                    ) AS lens
                    CROSS JOIN LATERAL jsonb_to_record(similarity) 
                    AS sim({sim_fields_sql})
                    WHERE {sim_conditions};
                """
            ) + '\n').format(
                lens=sql.Identifier(self._job.table_name(self._lens.id)),
                lens_sql=self._lens.sql,
                sim_fields_sql=sql.SQL(', ').join(sim_fields_sql),
                sim_conditions=sql.SQL(' AND ').join(self._lens.similarity_threshold_sqls)
            )

        return sql.SQL(cleandoc(
            """ DROP TABLE IF EXISTS lenses.{lens} CASCADE;
                CREATE TABLE lenses.{lens} AS
                {lens_sql};
            """
        ) + '\n').format(
            lens=sql.Identifier(self._job.table_name(self._lens.id)),
            lens_sql=self._lens.sql
        )

    def generate_lens_finish_sql(self):
        return sql.SQL(cleandoc(
            """ ALTER TABLE lenses.{lens}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id text;

                ALTER TABLE lenses.{lens} ADD COLUMN sort_order serial;

                CREATE INDEX ON lenses.{lens} USING hash (source_uri);
                CREATE INDEX ON lenses.{lens} USING hash (target_uri);
                CREATE INDEX ON lenses.{lens} USING hash (cluster_id);
                CREATE INDEX ON lenses.{lens} USING btree (sort_order);

                ANALYZE lenses.{lens};
            """) + '\n').format(lens=sql.Identifier(self._job.table_name(self._lens.id)))

    @property
    def sql_string(self):
        sql_str = get_string_from_sql(self.generate_lens_sql())
        sql_str += '\n'
        sql_str += get_string_from_sql(self.generate_lens_finish_sql())

        return sql_str
