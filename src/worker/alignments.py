import re
import time
import threading

from common.config_db import db_conn
from common.job_alignment import get_job_data, get_job_alignment, update_alignment_job

from psycopg2 import sql as psycopg2_sql, ProgrammingError

from worker.matching.linkset_sql import LinksetSql
from worker.matching.alignment_config import AlignmentConfig


class AlignmentJob:
    def __init__(self, job_id, alignment):
        self.job_id = job_id
        self.alignment = alignment

        self.killed = False
        self.status = None
        self.exception = None

        self.db_conn = None
        self.config = None
        self.linkset_sql = None

        self.reset()

    def reset(self):
        job_data = get_job_data(self.job_id)
        self.config = AlignmentConfig(self.job_id, self.alignment, job_data['mappings'], job_data['resources'])
        self.linkset_sql = LinksetSql(self.config)

    def run(self):
        while self.config.has_queued_resources:
            update_alignment_job(self.job_id, self.alignment, {'status': 'downloading'})
            time.sleep(1)
            self.reset()

        thread = threading.Thread(target=self.run_generated_sql)
        thread.start()

        while not self.killed and thread.is_alive():
            self.watch_process_counts()
            self.watch_kill()
            time.sleep(1)

        if self.killed:
            return

        if self.exception:
            err_message = str(self.exception)
            update_alignment_job(self.job_id, self.alignment, {'status': 'failed', 'status_message': err_message})
            self.cleanup()
        else:
            self.finish()

    def run_generated_sql(self):
        try:
            self.db_conn = db_conn()

            if not self.killed:
                schema_name_sql = psycopg2_sql.Identifier(self.config.linkset_schema_name)
                self.process_sql(psycopg2_sql.Composed([
                    psycopg2_sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
                    psycopg2_sql.SQL('SET SEARCH_PATH TO "$user", {}, public;\n').format(schema_name_sql),
                ]))

            if not self.killed and not self.linkset_sql.match_only:
                self.status = 'Generating resources'
                self.process_sql(self.linkset_sql.generate_resources())

            if not self.killed and not self.linkset_sql.resources_only:
                self.status = 'Generating indexes'
                self.process_sql(self.linkset_sql.generate_match_index_sql())

            if not self.killed and not self.linkset_sql.resources_only:
                self.status = 'Generating source resources'
                self.process_sql(self.linkset_sql.generate_match_source_sql())

            if not self.killed and not self.linkset_sql.resources_only:
                self.status = 'Generating target resources'
                self.process_sql(self.linkset_sql.generate_match_target_sql())

            if not self.killed and not self.linkset_sql.resources_only:
                self.status = 'Looking for links'
                self.process_sql(self.linkset_sql.generate_match_linkset_sql())
        except Exception as e:
            self.exception = e
        finally:
            self.db_conn.close()

    def process_sql(self, sql):
        sql_string = sql.as_string(self.db_conn)
        for statement in sql_string.split(';\n'):
            statement = statement.strip()

            if statement.startswith('--'):
                continue

            if re.search(r'\S', statement):
                if re.match(r'^\s*SELECT', statement) and not re.search(r'set_config\(', statement):
                    continue
                else:
                    with self.db_conn.cursor() as cur:
                        cur.execute(statement)
                        self.db_conn.commit()

    def kill(self, reset=True):
        self.killed = True

        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        update_alignment_job(self.job_id, self.alignment, job_data)

        if self.db_conn and not self.db_conn.closed:
            self.db_conn.cancel()
            # with db_conn() as conn, conn.cursor() as cur:
            #     cur.execute("SELECT pg_terminate_backend(%s)", (self.db_conn.get_backend_pid(),))
            #     conn.commit()

        self.cleanup()

    def watch_process_counts(self):
        with db_conn() as conn, conn.cursor() as cur:
            data = {'status_message': self.status}

            for suffix in ('_count', '_source_count', '_target_count'):
                sequence_name = self.config.match_to_run.name + suffix

                try:
                    cur.execute(psycopg2_sql.SQL('SELECT last_value FROM {}.{}').format(
                        psycopg2_sql.Identifier(self.config.linkset_schema_name),
                        psycopg2_sql.Identifier(sequence_name),
                    ))

                    inserted = cur.fetchone()[0]
                    if inserted:
                        if suffix == '_source_count':
                            data['sources_count'] = inserted
                        elif suffix == '_target_count':
                            data['targets_count'] = inserted
                        else:
                            data['links_count'] = inserted
                except ProgrammingError:
                    pass
                finally:
                    conn.commit()

        update_alignment_job(self.job_id, self.alignment, data)

    def watch_kill(self):
        alignment_job = get_job_alignment(self.job_id, self.alignment)
        if alignment_job['kill']:
            self.kill(reset=False)

    def finish(self):
        self.watch_process_counts()

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}').format(
                psycopg2_sql.Identifier(self.config.linkset_table_name)))
            links = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}.{}').format(
                psycopg2_sql.Identifier(self.config.linkset_schema_name),
                psycopg2_sql.Identifier(self.config.match_to_run.name + '_source')))
            sources = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}.{}').format(
                psycopg2_sql.Identifier(self.config.linkset_schema_name),
                psycopg2_sql.Identifier(self.config.match_to_run.name + '_target')))
            targets = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(self.config.linkset_schema_name)))

            if links == 0:
                cur.execute(psycopg2_sql.SQL('DROP TABLE {} CASCADE')
                            .format(psycopg2_sql.Identifier(self.config.linkset_table_name)))
                conn.commit()

            cur.execute("UPDATE alignments "
                        "SET status = %s, status_message = null, distinct_links_count = %s, "
                        "distinct_sources_count = %s, distinct_targets_count = %s, finished_at = now() "
                        "WHERE job_id = %s AND alignment = %s",
                        ('done', links, sources, targets, self.job_id, self.alignment))
            conn.commit()

            cur.execute('SELECT * FROM clusterings WHERE job_id = %s AND alignment = %s',
                        (self.job_id, self.alignment))
            clustering = cur.fetchone()

            if clustering:
                query = psycopg2_sql.SQL("""
                    UPDATE clusterings 
                    SET status = %s, requested_at = now(), processing_at = null, finished_at = null
                    WHERE job_id = %s AND alignment = %s
                """)

                cur.execute(query, ('waiting', self.job_id, self.alignment))
                conn.commit()
            else:
                query = psycopg2_sql.SQL("""
                    INSERT INTO clusterings 
                    (job_id, alignment, clustering_type, association_file, status, requested_at) 
                    VALUES (%s, %s, %s, %s, %s, now())
                """)

                cur.execute(query, (self.job_id, self.alignment, 'default', None, 'waiting'))
                conn.commit()

    def cleanup(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(self.config.linkset_schema_name)))
            conn.commit()
