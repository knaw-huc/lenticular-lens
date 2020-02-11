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
            source_name=sql.Identifier(self.config.match_to_run.name + '_source'),
            source_sequence_name=sql.Identifier(self.config.match_to_run.name + '_source_count'),
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
            target_name=sql.Identifier(self.config.match_to_run.name + '_target'),
            target_sequence_name=sql.Identifier(self.config.match_to_run.name + '_target_count'),
        )

    def generate_match_linkset_sql(self):
        return sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS {sequence_name} CASCADE;
                CREATE SEQUENCE {sequence_name} MINVALUE 0 START 0;
                
                DROP TABLE IF EXISTS public.{view_name} CASCADE;
                CREATE TABLE public.{view_name} AS
                SELECT source.uri AS source_uri, target.uri AS target_uri, 
                {strengths_field} AS strengths
                FROM {source_name} AS source
                JOIN {target_name} AS target
                ON (source.collection != target.collection OR source.uri > target.uri)
                AND {conditions} {match_against}
                AND increment_counter({sequence})
                GROUP BY source.uri, target.uri;
                
                ALTER TABLE public.{view_name}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN sort_order serial,
                ADD COLUMN cluster_id text,
                ADD COLUMN valid boolean;

                CREATE INDEX ON public.{view_name} USING hash (source_uri);
                CREATE INDEX ON public.{view_name} USING hash (target_uri);
                CREATE INDEX ON public.{view_name} USING hash (cluster_id);
                CREATE INDEX ON public.{view_name} USING hash (valid);
                CREATE INDEX ON public.{view_name} USING btree (sort_order);

                ANALYZE public.{view_name};
            """
        ) + '\n').format(
            strengths_field=self.config.match_to_run.similarity_fields_agg_sql,
            conditions=self.config.match_to_run.conditions_sql,
            match_against=self.config.match_to_run.match_against_sql,
            view_name=sql.Identifier(self.config.linkset_table_name),
            source_name=sql.Identifier(self.config.match_to_run.name + '_source'),
            target_name=sql.Identifier(self.config.match_to_run.name + '_target'),
            sequence_name=sql.Identifier(self.config.match_to_run.name + '_count'),
            sequence=sql.Literal(self.config.match_to_run.name + '_count')
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
