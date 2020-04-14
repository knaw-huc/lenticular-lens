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
                view_name=sql.Identifier(entity_type_selection.label),
                matching_fields=entity_type_selection.matching_fields_sql(self._linkset),
                table_name=sql.Identifier(entity_type_selection.table_name),
                joins=entity_type_selection.joins(self._linkset).sql,
                wheres=entity_type_selection.where_sql,
                limit=entity_type_selection.limit_sql,
            )

            entity_type_selections_sql.append(entity_type_selection_sql)

        return sql.Composed(entity_type_selections_sql)

    def generate_match_index_sql(self):
        return self._linkset.index_sql

    def generate_match_source_sql(self):
        return sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS {source_sequence_name} CASCADE;
                CREATE SEQUENCE {source_sequence_name} MINVALUE 1;
                
                DROP MATERIALIZED VIEW IF EXISTS {source_name} CASCADE;
                CREATE MATERIALIZED VIEW {source_name} AS 
                {source};
                
                CREATE INDEX ON {source_name} (uri);
                ANALYZE {source_name};
            """
        ) + '\n').format(
            source=self._linkset.source_sql,
            source_name=sql.Identifier('source'),
            source_sequence_name=sql.Identifier('source_count'),
        )

    def generate_match_target_sql(self):
        return sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS {target_sequence_name} CASCADE;
                CREATE SEQUENCE {target_sequence_name} MINVALUE 1;
                
                DROP MATERIALIZED VIEW IF EXISTS {target_name} CASCADE;
                CREATE MATERIALIZED VIEW {target_name} AS 
                {target};
                
                CREATE INDEX ON {target_name} (uri);
                ANALYZE {target_name};
            """
        ) + '\n').format(
            target=self._linkset.target_sql,
            target_name=sql.Identifier('target'),
            target_sequence_name=sql.Identifier('target_count'),
        )

    def generate_match_linkset_sql(self):
        return sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS {sequence_name} CASCADE;
                CREATE SEQUENCE {sequence_name} MINVALUE 1;
                
                DROP TABLE IF EXISTS public.{view_name} CASCADE;
                CREATE TABLE public.{view_name} AS
                SELECT  CASE WHEN source.uri < target.uri THEN source.uri ELSE target.uri END AS source_uri,
                        CASE WHEN source.uri < target.uri THEN target.uri ELSE source.uri END AS target_uri,
                        CASE WHEN every(source.uri < target.uri) THEN 'source_target'::link_order
                             WHEN every(target.uri < source.uri) THEN 'target_source'::link_order
                             ELSE 'both'::link_order END AS link_order,
                        ARRAY_AGG(DISTINCT source.collection) AS source_collections,
                        ARRAY_AGG(DISTINCT target.collection) AS target_collections,
                        {similarity_field} AS similarity
                FROM {source_name} AS source
                JOIN {target_name} AS target
                ON (source.uri != target.uri) 
                AND {conditions}
                AND increment_counter({sequence})
                GROUP BY source_uri, target_uri;

                ALTER TABLE public.{view_name}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id text,
                ADD COLUMN valid link_validity DEFAULT 'not_validated';

                ALTER TABLE public.{view_name} ADD COLUMN sort_order serial;

                CREATE INDEX ON public.{view_name} USING hash (source_uri);
                CREATE INDEX ON public.{view_name} USING hash (target_uri);
                CREATE INDEX ON public.{view_name} USING hash (cluster_id);
                CREATE INDEX ON public.{view_name} USING hash (valid);
                CREATE INDEX ON public.{view_name} USING btree (sort_order);

                ANALYZE public.{view_name};
            """
        ) + '\n').format(
            similarity_field=self._linkset.similarity_fields_agg_sql,
            conditions=self._linkset.conditions_sql,
            view_name=sql.Identifier(self._job.linkset_table_name(self._linkset.id)),
            source_name=sql.Identifier('source'),
            target_name=sql.Identifier('target'),
            sequence_name=sql.Identifier('linkset_count'),
            sequence=sql.Literal('linkset_count')
        )

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
        sql_str += get_string_from_sql(self.generate_match_index_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_linkset_sql())

        return sql_str
