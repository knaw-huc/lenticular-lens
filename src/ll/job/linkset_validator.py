from uuid import uuid4
from psycopg2 import sql

from ll.util.config_db import db_conn


class LinksetValidator:
    def __init__(self, job, spec, linkset_builder, with_view_filters=True, compute_similarity=False):
        self._job = job
        self._spec = spec
        self._cte_sql = linkset_builder.get_linkset_cte_sql(
            with_view_filters=with_view_filters, compute_similarity=compute_similarity,
            apply_paging=False, include_linkset_uris=False)

    def validate_lens(self, valid):
        with db_conn() as conn, conn.cursor() as cur:
            temp_table_id = uuid4().hex

            cur.execute(sql.SQL('''
                CREATE TEMPORARY TABLE {table_name} ON COMMIT DROP AS (
                    {cte_sql}
                    SELECT source_uri, target_uri FROM linkset
                )
            ''').format(
                table_name=sql.Identifier(temp_table_id),
                cte_sql=self._cte_sql,
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

    def validate_linkset(self, valid):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('''
                {cte_sql}
                 
                UPDATE linksets.{table_name} AS ls
                SET valid = {valid} 
                FROM linkset
                WHERE ls.source_uri = linkset.source_uri
                AND ls.target_uri = linkset.target_uri
            ''').format(
                cte_sql=self._cte_sql,
                table_name=sql.Identifier(self._job.table_name(self._spec.id)),
                valid=sql.Literal(valid))
            )

            # If links in a linkset are updated, then also update the same links from lenses based on this linkset
            # However, if the same link yield different validations among the linksets, then use 'mixed'
            for lens_spec in self._job.lens_specs:
                lens = self._job.lens(lens_spec.id)

                if lens and lens['status'] == 'done' and lens['links_count'] > 0 \
                        and self._spec.id in [linkset.id for linkset in lens_spec.linksets]:
                    validities_sql = sql.SQL(' UNION ALL ').join(
                        sql.SQL('''
                            SELECT ls.source_uri, ls.target_uri, ls.valid 
                            FROM linksets.{} AS ls
                            INNER JOIN linkset AS sel
                            ON ls.source_uri = sel.source_uri
                            AND ls.target_uri = sel.target_uri
                        ''').format(sql.Identifier(self._job.table_name(linkset.id)))
                        for linkset in lens_spec.linksets
                    )

                    cur.execute(sql.SQL('''
                        {cte_sql}
                        
                        UPDATE lenses.{lens_table} AS lens
                        SET valid = ls.valid
                        FROM (
                            SELECT source_uri, target_uri, 
                                   CASE WHEN count(DISTINCT valid) > 1 
                                        THEN 'mixed'::link_validity 
                                        ELSE min(valid) END AS valid
                            FROM ({validaties_select}) AS x
                            GROUP BY source_uri, target_uri
                        ) AS ls
                        WHERE lens.source_uri = ls.source_uri 
                        AND lens.target_uri = ls.target_uri 
                    ''').format(
                        cte_sql=self._cte_sql,
                        lens_table=sql.Identifier(self._job.table_name(lens_spec.id)),
                        validaties_select=validities_sql,
                    ))
