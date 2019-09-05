import re
import time
import locale
import datetime

from psycopg2 import sql
from inspect import cleandoc

from worker.matching.alignment_config import AlignmentConfig

from common.config_db import db_conn
from common.helpers import get_job_data

locale.setlocale(locale.LC_ALL, '')


class LinksetsCollection:
    def __init__(self, job_id, run_match, sql_only=False, resources_only=False, matches_only=False):
        self.job_id = job_id
        self.run_match = str(run_match)

        self.sql_only = sql_only
        self.resources_only = resources_only
        self.matches_only = matches_only

        self.status = None
        self.exception = None

        job_data = get_job_data(self.job_id)
        self.config = AlignmentConfig(self.run_match, job_data['mappings'], job_data['resources'])

    @property
    def view_name(self):
        for match in self.config.matches:
            if match.id == self.run_match:
                return match.name

        return None

    @property
    def has_queued_view(self):
        for resource in self.config.resources:
            if resource.view_queued:
                return True

        return False

    def run(self):
        try:
            open('%s_%s.sql' % (self.run_match, self.job_id), 'w').close()

            if not self.matches_only:
                self.generate_resources()
            if not self.resources_only and (not self.has_queued_view or self.sql_only):
                self.generate_matches()
        except Exception as e:
            self.exception = e
            raise e

    def generate_resources(self):
        if not self.has_queued_view or self.sql_only:
            for resource in self.config.resources_to_run:
                self.status = 'Generating collection %s.' % resource.label

                result = self.process_sql(self.generate_resource_sql(resource))

                self.status = 'Collection %s generated. Inserted %s records in %s' % (
                    resource.label,
                    locale.format_string('%i', result['affected'], grouping=True),
                    result['duration']
                )

    def generate_matches(self):
        for match in self.config.matches_to_run:
            self.status = 'Generating linkset %s.' % match.name

            result = self.process_sql(self.generate_match_sql(match), match.before_alignment)

            self.status = 'Linkset %s generated. %s links created in %s.' % (
                match.name,
                locale.format_string('%i', result['affected'], grouping=True),
                result['duration']
            )

    def process_sql(self, composed, inject=None):
        query_starting_time = time.time()

        schema_name_sql = sql.Identifier('job_' + self.run_match + '_' + self.job_id)
        composed = sql.Composed([
            sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
            sql.SQL('SET SEARCH_PATH TO "$user", {}, public;\n').format(schema_name_sql),
            composed,
        ])

        processed_count = 0
        affected_count = 0
        with db_conn() as conn:
            sql_string = composed.as_string(conn)
            inject = inject.as_string(conn) if inject else ''

            with open('%s_%s.sql' % (self.run_match, self.job_id), 'a') as sql_file:
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

                                if cur.rowcount > 0:
                                    affected_count += cur.rowcount

            return {'processed': processed_count, 'affected': affected_count,
                    'duration': str(datetime.timedelta(seconds=time.time() - query_starting_time))}

    @staticmethod
    def generate_resource_sql(resource):
        pre = sql.SQL('SELECT * FROM (') if resource.limit > -1 else sql.SQL('')

        sql_composed = sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
            
                CREATE MATERIALIZED VIEW {view_name} AS
                {pre}SELECT DISTINCT {matching_fields}
                FROM {table_name} AS {view_name}{joins}{wheres}
                ORDER BY uri{limit};
                
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
    def generate_match_sql(match):
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
                
                DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
                CREATE MATERIALIZED VIEW {view_name} AS
                SELECT source.uri AS source_uri, target.uri AS target_uri, {fields}
                FROM {source_name} AS source
                JOIN {target_name} AS target
                ON (source.collection != target.collection OR source.uri > target.uri)
                AND ({conditions})
                AND nextval({sequence}) != 0;
                
                ANALYZE {view_name};
                CREATE INDEX ON {view_name} (source_uri);
                CREATE INDEX ON {view_name} (target_uri);
                
                SELECT * FROM {view_name};
            """
        ))

        return match.index_sql + sql.SQL('\n') + sql_composed.format(
            source=match.source_sql,
            target=match.target_sql,
            fields=match.similarity_fields_sql,
            conditions=match.conditions_sql,
            view_name=sql.Identifier(match.name),
            source_name=sql.Identifier(match.name + '_source'),
            target_name=sql.Identifier(match.name + '_target'),
            sequence_name=sql.Identifier(match.name + '_count'),
            source_sequence_name=sql.Identifier(match.name + '_source_count'),
            target_sequence_name=sql.Identifier(match.name + '_target_count'),
            sequence=sql.Literal(match.name + '_count'),
            source_sequence=sql.Literal(match.name + '_source_count'),
            target_sequence=sql.Literal(match.name + '_target_count')
        )
