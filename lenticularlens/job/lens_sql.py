import locale

from psycopg import sql
from inspect import cleandoc

from lenticularlens.elem.matching_method import MatchingMethod
from lenticularlens.util.helpers import get_string_from_sql, get_sql_empty

locale.setlocale(locale.LC_ALL, '')


class LensSql:
    def __init__(self, job, id):
        self._job = job
        self._lens = job.get_lens_spec_by_id(id)

    def generate_lens_sql(self):
        def spec_select_sql(id, type):
            default_columns = sql.SQL('source_uri, target_uri, link_order, source_collections, target_collections, '
                                      'source_intermediates, target_intermediates, similarities, valid')

            if type == 'linkset':
                return sql.SQL('SELECT {default_columns}, ARRAY[{id}] AS linksets, ARRAY[]::integer[] AS lenses '
                               'FROM linksets.{table}').format(
                    default_columns=default_columns,
                    id=sql.Literal(id),
                    table=sql.Identifier(self._job.table_name(id))
                )

            return sql.SQL('SELECT {default_columns}, linksets, ARRAY[{id}] AS lenses '
                           'FROM lenses.{table}').format(
                default_columns=default_columns,
                id=sql.Literal(id),
                table=sql.Identifier(self._job.table_name(id))
            )

        lens_sql = self._lens.with_lenses_recursive(
            lambda elem: self._lens_sql(elem['type'], elem['only_left'],
                                        sql.SQL('(\n{sql}\n)').format(sql=elem['left']),
                                        sql.SQL('(\n{sql}\n)').format(sql=elem['right'])),
            lambda spec: spec_select_sql(spec['id'], spec['type'])
        )

        sim_fields_sqls = MatchingMethod.get_similarity_fields_sqls(self._lens.matching_methods)

        sim_conditions_sqls = [sql.SQL('{similarity} >= {threshold}')
                                   .format(similarity=similarity, threshold=sql.Literal(threshold))
                               for (threshold, similarity) in self._lens.similarity_logic_ops_sql_per_threshold]

        sim_condition_sql = get_sql_empty(sql.Composed([sql.SQL('WHERE '), sql.SQL(' AND ').join(sim_conditions_sqls)]),
                                          flag=sim_conditions_sqls)

        return sql.SQL(cleandoc(
            """ DROP TABLE IF EXISTS lenses.{lens} CASCADE;
                CREATE TABLE lenses.{lens} AS
                SELECT lens.*, similarity
                FROM (
                    {lens_sql}
                ) AS lens
                {sim_fields_sql}
                CROSS JOIN LATERAL coalesce({sim_logic_ops_sql}, 1) AS similarity 
                {sim_condition_sql};
            """
        ) + '\n').format(
            lens=sql.Identifier(self._job.table_name(self._lens.id)),
            lens_sql=lens_sql,
            sim_fields_sql=sql.SQL('\n').join(sim_fields_sqls),
            sim_logic_ops_sql=self._lens.similarity_logic_ops_sql,
            sim_condition_sql=sim_condition_sql
        )

    def generate_lens_finish_sql(self):
        return sql.SQL(cleandoc(
            """ ALTER TABLE lenses.{lens}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id integer,
                ADD COLUMN cluster_hash_id char(15),
                ADD COLUMN motivation text;

                ALTER TABLE lenses.{lens} ADD COLUMN sort_order serial;

                CREATE INDEX ON lenses.{lens} USING hash (source_uri);
                CREATE INDEX ON lenses.{lens} USING hash (target_uri);
                CREATE INDEX ON lenses.{lens} USING hash (valid);
                
                CREATE INDEX ON lenses.{lens} USING btree (cluster_id);
                CREATE INDEX ON lenses.{lens} USING btree (similarity);
                CREATE INDEX ON lenses.{lens} USING btree (sort_order);

                ANALYZE lenses.{lens};
            """
        ) + '\n').format(lens=sql.Identifier(self._job.table_name(self._lens.id)))

    @property
    def sql_string(self):
        sql_str = get_string_from_sql(self.generate_lens_sql())
        sql_str += '\n'
        sql_str += get_string_from_sql(self.generate_lens_finish_sql())

        return sql_str

    @staticmethod
    def _lens_sql(type, only_left, left_sql, right_sql):
        return LensSql._with_select_sql(type, cleandoc('''
            SELECT l.source_uri, l.target_uri, l.link_order, l.source_collections, l.target_collections, 
                   l.source_intermediates, l.target_intermediates, l.linksets, l.lenses, l.similarities, l.valid
        ''') if only_left else cleandoc('''
            SELECT
                coalesce(l.source_uri, r.source_uri) AS source_uri,
                coalesce(l.target_uri, r.target_uri) AS target_uri,
                CASE WHEN l.link_order = r.link_order THEN l.link_order 
                     WHEN l.link_order IS NULL THEN r.link_order 
                     WHEN r.link_order IS NULL THEN l.link_order 
                     ELSE 'both'::link_order END AS link_order,
                coalesce(array_distinct_merge(l.source_collections, r.source_collections), 
                         l.source_collections, r.source_collections) AS source_collections,
                coalesce(array_distinct_merge(l.target_collections, r.target_collections), 
                         l.target_collections, r.target_collections) AS target_collections,
                coalesce(jsonb_merge(l.source_intermediates, r.source_intermediates), 
                         l.source_intermediates, r.source_intermediates) AS source_intermediates,
                coalesce(jsonb_merge(l.target_intermediates, r.target_intermediates), 
                         l.target_intermediates, r.target_intermediates) AS target_intermediates,
                coalesce(array_distinct_merge(l.linksets, r.linksets), l.linksets, r.linksets) AS linksets,
                coalesce(array_distinct_merge(l.lenses, r.lenses), l.lenses, r.lenses) AS lenses,
                coalesce(jsonb_merge(l.similarities, r.similarities), l.similarities, r.similarities) AS similarities,
                CASE WHEN l.valid = r.valid THEN l.valid 
                     WHEN l.valid IS NULL THEN r.valid 
                     WHEN r.valid IS NULL THEN l.valid
                     ELSE 'disputed'::link_validity END AS valid
        '''), left_sql, right_sql)

    @staticmethod
    def _with_select_sql(type, select_sql, left_sql, right_sql):
        if type == 'union':
            return sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                FULL JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
            ''')).format(left=left_sql, right=right_sql)
        elif type == 'intersection':
            return sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                INNER JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
            ''')).format(left=left_sql, right=right_sql)
        elif type == 'difference':
            return sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                LEFT JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
                WHERE r.source_uri IS NULL AND r.target_uri IS NULL
            ''')).format(left=left_sql, right=right_sql)
        elif type == 'sym_difference':
            return sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                FULL JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
                WHERE (l.source_uri IS NULL AND l.target_uri IS NULL) 
                OR (r.source_uri IS NULL AND r.target_uri IS NULL)
            ''')).format(left=left_sql, right=right_sql)
        elif type == 'in_set_and':
            return sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                WHERE EXISTS (
                    SELECT 1
                    FROM {right} AS in_set 
                    WHERE l.source_uri IN (in_set.source_uri, in_set.target_uri)
                    LIMIT 1
                )
                AND EXISTS (
                    SELECT 1
                    FROM {right} AS in_set 
                    WHERE l.target_uri IN (in_set.source_uri, in_set.target_uri)
                    LIMIT 1
                )
            ''')).format(left=left_sql, right=right_sql)
        elif type == 'in_set_or':
            return sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                WHERE EXISTS (
                    SELECT 1
                    FROM {right} AS in_set 
                    WHERE l.source_uri IN (in_set.source_uri, in_set.target_uri)
                    OR l.target_uri IN (in_set.source_uri, in_set.target_uri)
                    LIMIT 1
                )
            ''')).format(left=left_sql, right=right_sql)
        elif type == 'in_set_source':
            return sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                WHERE EXISTS (
                    SELECT 1
                    FROM {right} AS in_set 
                    WHERE l.source_uri IN (in_set.source_uri, in_set.target_uri)
                    LIMIT 1
                )
            ''')).format(left=left_sql, right=right_sql)
        elif type == 'in_set_target':
            return sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                WHERE EXISTS (
                    SELECT 1
                    FROM {right} AS in_set 
                    WHERE l.target_uri IN (in_set.source_uri, in_set.target_uri)
                    LIMIT 1
                )
            ''')).format(left=left_sql, right=right_sql)
