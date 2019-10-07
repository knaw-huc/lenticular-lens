import re
import locale

from psycopg2 import sql
from inspect import cleandoc

from worker.matching.alignment_config import AlignmentConfig

from common.config_db import db_conn
from common.job_alignment import get_job_data

locale.setlocale(locale.LC_ALL, '')


class LinksetsCollection:
    def __init__(self, job_id, run_match, sql_only=False, resources_only=False, match_only=False):
        self.job_id = job_id
        self.run_match = run_match

        self.sql_only = sql_only
        self.resources_only = resources_only
        self.match_only = match_only

        self.exception = None

        job_data = get_job_data(self.job_id)
        self.config = AlignmentConfig(self.job_id, self.run_match, job_data['mappings'], job_data['resources'])

    @property
    def view_name(self):
        return self.config.match_to_run.name

    @property
    def has_queued_view(self):
        for resource in self.config.resources:
            if resource.view_queued:
                return True

        return False

    def run(self):
        try:
            open('%s_%s.sql' % (str(self.run_match), self.job_id), 'w').close()

            if not self.match_only:
                self.generate_resources()
            if not self.resources_only and (not self.has_queued_view or self.sql_only):
                self.generate_match()
        except Exception as e:
            self.exception = e
            raise e

    def generate_resources(self):
        if not self.has_queued_view or self.sql_only:
            for resource in self.config.resources_to_run:
                self.process_sql(self.generate_resource_sql(resource))

    def generate_match(self):
        table_name = 'linkset_' + self.job_id + '_' + str(self.run_match)
        self.process_sql(self.generate_match_sql(self.config.match_to_run, table_name),
                         self.config.match_to_run.before_alignment)

    def process_sql(self, composed, inject=None):
        schema_name_sql = sql.Identifier('job_' + str(self.run_match) + '_' + self.job_id)
        composed = sql.Composed([
            sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
            sql.SQL('SET SEARCH_PATH TO "$user", {}, public;\n').format(schema_name_sql),
            composed,
        ])

        with db_conn() as conn:
            sql_string = composed.as_string(conn)
            inject = inject.as_string(conn) if inject else ''

            with open('%s_%s.sql' % (str(self.run_match), self.job_id), 'a') as sql_file:
                sql_file.write(sql_string)

            if not self.sql_only:
                for statement in sql_string.split(';\n'):
                    statement = statement.strip()

                    if statement.startswith('--'):
                        continue

                    if re.search(r'\S', statement):
                        if re.match(r'^\s*SELECT', statement) and not re.search(r'set_config\(', statement):
                            continue
                        else:
                            with conn.cursor() as cur:
                                if inject:
                                    cur.execute(inject)
                                    conn.commit()

                                cur.execute(statement)
                                conn.commit()

    @staticmethod
    def generate_resource_sql(resource):
        pre = sql.SQL('SELECT * FROM (') if resource.limit > -1 else sql.SQL('')

        sql_composed = sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
            
                CREATE MATERIALIZED VIEW {view_name} AS
                {pre}SELECT DISTINCT {matching_fields}
                FROM {table_name} AS {view_name} {joins} {wheres}
                ORDER BY uri {limit};
                
                ANALYZE {view_name};
            """
        ))

        return sql_composed.format(
            pre=pre,
            view_name=sql.Identifier(resource.label),
            matching_fields=resource.matching_fields_sql,
            table_name=sql.Identifier(resource.collection.table_name),
            joins=resource.joins_sql,
            wheres=resource.where_sql,
            limit=resource.limit_sql
        )

    @staticmethod
    def generate_match_sql(match, table_name):
        sql_composed = sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS {source_sequence_name} CASCADE;
                CREATE SEQUENCE {source_sequence_name} MINVALUE 0 START 0;
                
                DROP MATERIALIZED VIEW IF EXISTS {source_name} CASCADE;
                CREATE MATERIALIZED VIEW {source_name} AS 
                SELECT * 
                FROM ({source}) AS x
                WHERE nextval({source_sequence}) != 0;
                
                ANALYZE {source_name};
                CREATE INDEX ON {source_name} (uri);
                
                DROP SEQUENCE IF EXISTS {target_sequence_name} CASCADE;
                CREATE SEQUENCE {target_sequence_name} MINVALUE 0 START 0;
                
                DROP MATERIALIZED VIEW IF EXISTS {target_name} CASCADE;
                CREATE MATERIALIZED VIEW {target_name} AS 
                SELECT * 
                FROM ({target}) AS x
                WHERE nextval({target_sequence}) != 0;
                
                ANALYZE {target_name};
                CREATE INDEX ON {target_name} (uri);
                
                DROP SEQUENCE IF EXISTS {sequence_name} CASCADE;
                CREATE SEQUENCE {sequence_name} MINVALUE 0 START 0;
                
                DROP TABLE IF EXISTS public.{view_name} CASCADE;
                CREATE TABLE public.{view_name} AS                
                SELECT DISTINCT source.uri AS source_uri, target.uri AS target_uri, {strength_field}
                FROM {source_name} AS source
                JOIN {target_name} AS target
                ON (source.collection != target.collection OR source.uri > target.uri)
                AND {conditions} {match_against}
                AND nextval({sequence}) != 0;
                
                ALTER TABLE public.{view_name}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id text,
                ADD COLUMN valid boolean;

                CREATE INDEX ON public.{view_name} (source_uri);
                CREATE INDEX ON public.{view_name} (target_uri);
                CREATE INDEX ON public.{view_name} (cluster_id);

                ANALYZE public.{view_name};
            """
        ))

        return match.index_sql + sql.SQL('\n') + sql_composed.format(
            source=match.source_sql,
            target=match.target_sql,
            strength_field=match.strength_field_sql,
            conditions=match.conditions_sql,
            match_against=match.match_against_sql,
            view_name=sql.Identifier(table_name),
            source_name=sql.Identifier(match.name + '_source'),
            target_name=sql.Identifier(match.name + '_target'),
            sequence_name=sql.Identifier(match.name + '_count'),
            source_sequence_name=sql.Identifier(match.name + '_source_count'),
            target_sequence_name=sql.Identifier(match.name + '_target_count'),
            sequence=sql.Literal(match.name + '_count'),
            source_sequence=sql.Literal(match.name + '_source_count'),
            target_sequence=sql.Literal(match.name + '_target_count')
        )
