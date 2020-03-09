import locale

from psycopg2 import sql
from inspect import cleandoc
from ll.util.helpers import get_string_from_sql

locale.setlocale(locale.LC_ALL, '')


class MatchingSql:
    def __init__(self, config):
        self.config = config

    def generate_schema_sql(self):
        schema_name_sql = sql.Identifier(self.config.linkset_schema_name)

        return sql.Composed([
            sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
            sql.SQL('SET SEARCH_PATH TO "$user", {}, public;').format(schema_name_sql),
        ])

    def generate_resources_sql(self):
        resources_sql = []
        for resource in self.config.resources_to_run:
            pre = sql.SQL('SELECT * FROM (') if resource.limit > -1 else sql.SQL('')

            resource_sql = sql.SQL(cleandoc(
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
                view_name=sql.Identifier(resource.label),
                matching_fields=resource.matching_fields_sql,
                table_name=sql.Identifier(resource.table_name),
                joins=resource.joins.sql,
                wheres=resource.where_sql,
                limit=resource.limit_sql,
            )

            resources_sql.append(resource_sql)

        return sql.Composed(resources_sql)

    def generate_match_index_sql(self):
        return self.config.match_to_run.index_sql

    def generate_match_source_sql(self):
        return sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS {source_sequence_name} CASCADE;
                CREATE SEQUENCE {source_sequence_name} MINVALUE 0 START 0;
                
                DROP MATERIALIZED VIEW IF EXISTS {source_name} CASCADE;
                CREATE MATERIALIZED VIEW {source_name} AS 
                {source};
                
                CREATE INDEX ON {source_name} (uri);
                ANALYZE {source_name};
            """
        ) + '\n').format(
            source=self.config.match_to_run.source_sql,
            source_name=sql.Identifier('source'),
            source_sequence_name=sql.Identifier('source_count'),
        )

    def generate_match_target_sql(self):
        return sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS {target_sequence_name} CASCADE;
                CREATE SEQUENCE {target_sequence_name} MINVALUE 0 START 0;
                
                DROP MATERIALIZED VIEW IF EXISTS {target_name} CASCADE;
                CREATE MATERIALIZED VIEW {target_name} AS 
                {target};
                
                CREATE INDEX ON {target_name} (uri);
                ANALYZE {target_name};
            """
        ) + '\n').format(
            target=self.config.match_to_run.target_sql,
            target_name=sql.Identifier('target'),
            target_sequence_name=sql.Identifier('target_count'),
        )

    def generate_match_linkset_sql(self):
        return sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS {sequence_name} CASCADE;
                CREATE SEQUENCE {sequence_name} MINVALUE 0 START 0;
                
                DROP TABLE IF EXISTS public.{view_name} CASCADE;
                CREATE TABLE public.{view_name} AS
                SELECT  CASE WHEN source.uri < target.uri THEN source.uri ELSE target.uri END AS source_uri,
                        CASE WHEN source.uri < target.uri THEN target.uri ELSE source.uri END AS target_uri,
                        CASE WHEN every(source.uri < target.uri) THEN 'source_target'::link_order
                             WHEN every(target.uri < source.uri) THEN 'target_source'::link_order
                             ELSE 'both'::link_order END AS link_order,
                        ARRAY_AGG(DISTINCT combined.collection) AS collections,
                        {similarity_field} AS similarity
                FROM {source_name} AS source
                JOIN {target_name} AS target
                ON (source.uri != target.uri) 
                AND {conditions} {match_against}
                AND increment_counter({sequence})
                CROSS JOIN LATERAL (VALUES (source.collection), (target.collection)) AS combined(collection)
                GROUP BY source_uri, target_uri;

                ALTER TABLE public.{view_name}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id text,
                ADD COLUMN valid boolean;

                ALTER TABLE public.{view_name} ADD COLUMN sort_order serial;

                CREATE INDEX ON public.{view_name} USING hash (source_uri);
                CREATE INDEX ON public.{view_name} USING hash (target_uri);
                CREATE INDEX ON public.{view_name} USING hash (cluster_id);
                CREATE INDEX ON public.{view_name} USING hash (valid);
                CREATE INDEX ON public.{view_name} USING btree (sort_order);

                ANALYZE public.{view_name};
            """
        ) + '\n').format(
            similarity_field=self.config.match_to_run.similarity_fields_agg_sql,
            conditions=self.config.match_to_run.conditions_sql,
            match_against=self.config.match_to_run.match_against_sql,
            view_name=sql.Identifier(self.config.linkset_table_name),
            source_name=sql.Identifier('source'),
            target_name=sql.Identifier('target'),
            sequence_name=sql.Identifier('linkset_count'),
            sequence=sql.Literal('linkset_count')
        )

    @property
    def sql_string(self):
        sql_str = get_string_from_sql(self.generate_schema_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_resources_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_source_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_target_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_index_sql())
        sql_str += '\n\n'
        sql_str += get_string_from_sql(self.generate_match_linkset_sql())

        return sql_str
