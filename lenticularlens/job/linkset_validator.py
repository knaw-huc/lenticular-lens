from uuid import uuid4
from psycopg import sql

from lenticularlens.util.config_db import conn_pool


class LinksetValidator:
    def __init__(self, job, type, spec, linkset_builder, with_view_filters=True):
        self._job = job
        self._type = type
        self._spec = spec
        self._from_sql = linkset_builder.get_linkset_from_sql()
        self._filters_sql = linkset_builder.get_linkset_view_filters() if with_view_filters else sql.SQL('')

    def validate(self, valid):
        if self._type == 'lens':
            self._validate_lens(valid)
        else:
            self._validate_linkset(valid)

    def add_motivation(self, motivation):
        motivation = motivation.strip() if motivation is not None and motivation.strip() else None

        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('''
                UPDATE {schema}.{table_name} AS linkset
                SET motivation = {motivation}
                {filters_sql}
            ''').format(
                schema=sql.Identifier('linksets' if self._type == 'linkset' else 'lenses'),
                table_name=sql.Identifier(self._job.table_name(self._spec.id)),
                motivation=sql.Literal(motivation),
                filters_sql=self._filters_sql,
            ))

    def _validate_lens(self, valid):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            temp_table_id = uuid4().hex

            cur.execute(sql.SQL('''
                CREATE TEMPORARY TABLE {table_name} ON COMMIT DROP AS (
                    SELECT source_uri, target_uri
                    {from_sql}
                    {filters_sql}
                )
            ''').format(
                table_name=sql.Identifier(temp_table_id),
                from_sql=self._from_sql,
                filters_sql=self._filters_sql,
            ))

            # If links in a lens are updated, then also update the same links from the originating linksets/lenses
            update_sqls = [
                sql.SQL('''
                    UPDATE {schema}.{table_name} AS trg
                    SET valid = {valid} 
                    FROM {selection_table_name} AS sel
                    WHERE trg.source_uri = sel.source_uri 
                    AND trg.target_uri = sel.target_uri;
                ''').format(
                    schema=sql.Identifier(schema),
                    table_name=sql.Identifier(self._job.table_name(spec.id)),
                    valid=sql.Literal(valid),
                    selection_table_name=sql.Identifier(temp_table_id)
                )
                for (schema, selection) in [('linksets', self._spec.linksets), ('lenses', self._spec.lenses)]
                for spec in selection
            ]

            update_sqls.append(sql.SQL('''
                UPDATE lenses.{table_name} AS lens 
                SET valid = {valid}
                FROM {selection_table_name} AS sel
                WHERE lens.source_uri = sel.source_uri
                AND lens.target_uri = sel.target_uri;
            ''').format(
                table_name=sql.Identifier(self._job.table_name(self._spec.id)),
                valid=sql.Literal(valid),
                selection_table_name=sql.Identifier(temp_table_id)
            ))

            cur.execute(sql.Composed(update_sqls))

    def _validate_linkset(self, valid):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('''
                UPDATE linksets.{table_name} AS linkset
                SET valid = {valid}
                {filters_sql}
            ''').format(
                table_name=sql.Identifier(self._job.table_name(self._spec.id)),
                valid=sql.Literal(valid),
                filters_sql=self._filters_sql,
            ))

            # If links in a linkset are updated, then also update the same links from lenses based on this linkset
            # However, if the same link yield different validations among the linksets, then use 'disputed'
            for lens_spec in self._job.lens_specs:
                lens = self._job.lens(lens_spec.id)

                if lens and lens['status'] == 'done' and lens['links_count'] > 0 \
                        and self._spec.id in [linkset.id for linkset in lens_spec.linksets]:
                    validities_sql = sql.SQL(' UNION ALL ').join(
                        sql.SQL('''
                            SELECT ls.source_uri, ls.target_uri, ls.valid
                            {from_sql}
                            {filters_sql}
                            INNER JOIN linksets.{linkset_table} AS ls
                            ON ls.source_uri = linkset.source_uri
                            AND ls.target_uri = linkset.target_uri
                        ''').format(
                            from_sql=self._from_sql,
                            filters_sql=self._filters_sql,
                            linkset_table=sql.Identifier(self._job.table_name(linkset.id))
                        )
                        for linkset in lens_spec.linksets
                    )

                    cur.execute(sql.SQL('''
                        UPDATE lenses.{lens_table} AS lens
                        SET valid = ls.valid
                        FROM (
                            SELECT source_uri, target_uri, 
                                   CASE WHEN count(DISTINCT valid) > 1 
                                        THEN 'disputed'::link_validity 
                                        ELSE min(valid) END AS valid
                            FROM ({validaties_select}) AS x
                            GROUP BY source_uri, target_uri
                        ) AS ls
                        WHERE lens.source_uri = ls.source_uri 
                        AND lens.target_uri = ls.target_uri 
                    ''').format(
                        lens_table=sql.Identifier(self._job.table_name(lens_spec.id)),
                        validaties_select=validities_sql,
                    ))
