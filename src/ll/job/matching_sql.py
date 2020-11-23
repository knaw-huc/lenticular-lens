import locale

from psycopg2 import sql
from inspect import cleandoc
from ll.util.helpers import get_string_from_sql

locale.setlocale(locale.LC_ALL, '')


class MatchingSql:
    def __init__(self, job, id):
        self._job = job
        self._linkset = job.get_linkset_spec_by_id(id)

    def generate_schema_sql(self):
        schema_name_sql = sql.Identifier(self._job.linkset_schema_name(self._linkset.id))

        return sql.Composed([
            sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
            sql.SQL('SET SEARCH_PATH TO "$user", {}, public;').format(schema_name_sql),
        ])

    def generate_entity_type_selection_sql(self):
        entity_type_selections_sql = []
        for entity_type_selection in self._job.entity_type_selections_required_for_linkset(self._linkset.id):
            pre = sql.SQL('SELECT * FROM (') if entity_type_selection.limit > -1 else sql.SQL('')

            entity_type_selection_sql = sql.SQL(cleandoc(
                """ DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
                    CREATE MATERIALIZED VIEW {view_name} AS
                    {pre}SELECT DISTINCT {matching_fields}
                    FROM {table_name} AS {view_name} 
                    {joins} 
                    {wheres}
                    ORDER BY uri {limit};
                    
                    ANALYZE {view_name};
                """
            ) + '\n').format(
                pre=pre,
                view_name=sql.Identifier(entity_type_selection.internal_id),
                matching_fields=entity_type_selection.matching_fields_sql(self._linkset),
                table_name=sql.Identifier(entity_type_selection.table_name),
                joins=entity_type_selection.joins(self._linkset).sql,
                wheres=entity_type_selection.where_sql,
                limit=entity_type_selection.limit_sql,
            )

            entity_type_selections_sql.append(entity_type_selection_sql)

        return sql.Composed(entity_type_selections_sql)

    def generate_match_source_sql(self):
        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS source CASCADE;
                CREATE MATERIALIZED VIEW source AS 
                {};
                
                CREATE INDEX ON source (uri);
                ANALYZE source;
            """
        ) + '\n').format(self._linkset.source_sql)

    def generate_match_target_sql(self):
        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS target CASCADE;
                CREATE MATERIALIZED VIEW target AS 
                {};
                
                CREATE INDEX ON target (uri);
                ANALYZE target;
            """
        ) + '\n').format(self._linkset.target_sql)

    def generate_match_index_and_sequence_sql(self):
        sequence_sql = sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS linkset_count CASCADE;
                CREATE SEQUENCE linkset_count MINVALUE 1;
            """) + '\n')

        if self._linkset.index_sql:
            return sql.SQL('\n').join([self._linkset.index_sql, sequence_sql])

        return sequence_sql

    def generate_match_linkset_sql(self):
        # join_conditions = self._linkset.join_conditions_sql
        # join_conditions_sql = sql.SQL('AND {}').format(join_conditions) if join_conditions else sql.SQL('')
        #
        # match_conditions = self._linkset.match_conditions_sql
        # match_conditions_sql = sql.SQL('WHERE {}').format(match_conditions) if match_conditions else sql.SQL('')
        #
        # if match_conditions:
        #     match_conditions_sql = sql.SQL("{} \nAND increment_counter('linkset_count')").format(match_conditions_sql)
        # else:
        #     join_conditions_sql = sql.SQL("{} \nAND increment_counter('linkset_count')").format(join_conditions_sql)

        similarity_fields = self._linkset.similarity_fields
        if similarity_fields:
            similarities_sql = sql.SQL(cleandoc('''
                CROSS JOIN LATERAL (
                    SELECT {expressions}
                ) AS similarities ({names})
            ''')).format(
                expressions=sql.SQL(',\n    ').join(
                    [sim_expression for sim_expression in list(similarity_fields.values())]),
                names=sql.SQL(', ').join(
                    [sql.Identifier(sim_field) for sim_field in list(similarity_fields.keys())])
            )
        else:
            similarities_sql = sql.SQL('')

        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS linkset CASCADE;
                CREATE MATERIALIZED VIEW linkset AS
                SELECT CASE WHEN source.uri < target.uri THEN source.uri ELSE target.uri END AS source_uri,
                       CASE WHEN source.uri < target.uri THEN target.uri ELSE source.uri END AS target_uri,
                       CASE WHEN source.uri < target.uri 
                            THEN 'source_target'::link_order
                            ELSE 'target_source'::link_order END AS link_order,
                       source.collection AS source_collection,
                       target.collection AS target_collection
                FROM source
                JOIN target ON (source.uri != target.uri)
                {similarities}
                WHERE {conditions}
                AND increment_counter('linkset_count');
            """) + '\n').format(
            similarities=similarities_sql,
            conditions=self._linkset.conditions_sql
        )

    def generate_match_distinct_linkset_sql(self):
        return sql.SQL(cleandoc(
            """ DROP TABLE IF EXISTS public.{view_name} CASCADE;
                CREATE TABLE public.{view_name} AS
                SELECT source_uri, target_uri,
                       CASE WHEN every(link_order = 'source_target'::link_order) THEN 'source_target'::link_order
                            WHEN every(link_order = 'target_source'::link_order) THEN 'target_source'::link_order
                            ELSE 'both'::link_order END AS link_order,
                       array_agg(DISTINCT source_collection) AS source_collections,
                       array_agg(DISTINCT target_collection) AS target_collections,
                       {similarity} AS similarity
                FROM linkset
                GROUP BY source_uri, target_uri;
            """) + '\n').format(
            view_name=sql.Identifier(self._job.linkset_table_name(self._linkset.id)),
            similarity=self._linkset.similarity_sql,
            similarities=similarities_sql,
            conditions=self._linkset.conditions_sql
        )

    def generate_match_linkset_finish_sql(self):
        return sql.SQL(cleandoc(
            """ ALTER TABLE public.{linkset}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id text,
                ADD COLUMN valid link_validity DEFAULT 'not_validated';

                ALTER TABLE public.{linkset} ADD COLUMN sort_order serial;

                CREATE INDEX ON public.{linkset} USING hash (source_uri);
                CREATE INDEX ON public.{linkset} USING hash (target_uri);
                CREATE INDEX ON public.{linkset} USING hash (cluster_id);
                CREATE INDEX ON public.{linkset} USING hash (valid);
                CREATE INDEX ON public.{linkset} USING btree (sort_order);

                ANALYZE public.{linkset};
            """) + '\n').format(linkset=sql.Identifier(self._job.linkset_table_name(self._linkset.id)))

    @property
    def sql_string(self):
        sql_str = get_string_from_sql(self.generate_schema_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_entity_type_selection_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_source_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_target_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_index_and_sequence_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_linkset_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_linkset_finish_sql())

        return sql_str
