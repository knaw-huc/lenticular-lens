import locale

from psycopg2 import sql
from inspect import cleandoc

locale.setlocale(locale.LC_ALL, '')


class LinksetSql:
    def __init__(self, config):
        self.config = config

    def generate_schema(self):
        schema_name_sql = sql.Identifier(self.config.linkset_schema_name)

        return sql.Composed([
            sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
            sql.SQL('SET SEARCH_PATH TO "$user", {}, public;\n').format(schema_name_sql),
        ])

    def generate_resources(self):
        resources_sql = []
        for resource in self.config.resources_to_run:
            pre = sql.SQL('SELECT * FROM (') if resource.limit > -1 else sql.SQL('')

            resource_sql = sql.SQL(cleandoc(
                """ DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
                
                    CREATE MATERIALIZED VIEW {view_name} AS
                    {pre}SELECT DISTINCT {matching_fields}
                    FROM {table_name} AS {view_name} {joins} {wheres}
                    ORDER BY uri {limit};
                    
                    ANALYZE {view_name};
                """
            )).format(
                pre=pre,
                view_name=sql.Identifier(resource.label),
                matching_fields=resource.matching_fields_sql,
                table_name=sql.Identifier(resource.table_name),
                joins=resource.joins_sql,
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
                
                ANALYZE {source_name};
                CREATE INDEX ON {source_name} (uri);
            """
        )).format(
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
                
                ANALYZE {target_name};
                CREATE INDEX ON {target_name} (uri);
            """
        )).format(
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
                ADD COLUMN cluster_id text,
                ADD COLUMN valid boolean;

                CREATE INDEX ON public.{view_name} (cluster_id);
                ANALYZE public.{view_name};
            """
        )).format(
            strengths_field=self.config.match_to_run.similarity_fields_agg_sql,
            conditions=self.config.match_to_run.conditions_sql,
            match_against=self.config.match_to_run.match_against_sql,
            view_name=sql.Identifier(self.config.linkset_table_name),
            source_name=sql.Identifier(self.config.match_to_run.name + '_source'),
            target_name=sql.Identifier(self.config.match_to_run.name + '_target'),
            sequence_name=sql.Identifier(self.config.match_to_run.name + '_count'),
            sequence=sql.Literal(self.config.match_to_run.name + '_count')
        )

    def sql_string(self, conn):
        sql_str = self.generate_schema().as_string(conn)
        sql_str += self.generate_resources().as_string(conn)
        sql_str += self.generate_match_index_sql().as_string(conn)
        sql_str += self.generate_match_source_sql().as_string(conn)
        sql_str += self.generate_match_target_sql().as_string(conn)
        sql_str += self.generate_match_linkset_sql().as_string(conn)

        return sql_str


if __name__ == '__main__':
    from common.config_db import db_conn
    from common.job_alignment import get_job_data
    from worker.matching.alignment_config import AlignmentConfig

    job_data = get_job_data('workshop_1_1')
    config = AlignmentConfig('workshop_1_1', 7, job_data['mappings'], job_data['resources'])
    linkset_sql = LinksetSql(config)

    print(linkset_sql.sql_string(db_conn()))
