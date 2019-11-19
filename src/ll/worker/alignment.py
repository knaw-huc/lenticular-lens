import re
import time

from psycopg2 import sql as psycopg2_sql, ProgrammingError

from ll.job.job_sql import JobSql
from ll.job.job_config import JobConfig
from ll.job.job_alignment import get_job_data, get_job_alignment, update_alignment_job

from ll.worker.job import Job
from ll.util.config_db import db_conn


class AlignmentJob(Job):
    def __init__(self, job_id, alignment):
        self.job_id = job_id
        self.alignment = alignment

        self.config = None
        self.job_sql = None

        self.reset()
        super().__init__(self.run_generated_sql)

    def reset(self):
        job_data = get_job_data(self.job_id)
        self.config = JobConfig(self.job_id, job_data['resources'], job_data['mappings'], self.alignment)
        self.job_sql = JobSql(self.config)

    def run(self):
        download_status_set = False
        while self.config.has_queued_resources and not self.killed:
            if not download_status_set:
                update_alignment_job(self.job_id, self.alignment, {'status': 'downloading'})
                download_status_set = True

            time.sleep(1)
            self.reset()

        super().run()

    def run_generated_sql(self):
        if not self.killed:
            self.process_sql(self.job_sql.generate_schema())

        if not self.killed:
            self.status = 'Generating collections'
            self.process_sql(self.job_sql.generate_resources())

        if not self.killed:
            self.status = 'Generating indexes'
            self.process_sql(self.job_sql.generate_match_index_sql())

        if not self.killed:
            self.status = 'Generating source resources'
            self.process_sql(self.job_sql.generate_match_source_sql())

        if not self.killed:
            self.status = 'Generating target resources'
            self.process_sql(self.job_sql.generate_match_target_sql())

        if not self.killed:
            self.status = 'Looking for links'
            self.process_sql(self.job_sql.generate_match_linkset_sql())

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

    def watch_process(self):
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

    def on_kill(self, reset):
        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        update_alignment_job(self.job_id, self.alignment, job_data)

        self.cleanup()

    def on_exception(self):
        err_message = str(self.exception)
        update_alignment_job(self.job_id, self.alignment, {'status': 'failed', 'status_message': err_message})

        self.cleanup()

    def on_finish(self):
        self.watch_process()

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
                    SET status = %s, kill = false, requested_at = now(), processing_at = null, finished_at = null
                    WHERE job_id = %s AND alignment = %s
                """)

                cur.execute(query, ('waiting', self.job_id, self.alignment))
                conn.commit()
            else:
                query = psycopg2_sql.SQL("""
                    INSERT INTO clusterings 
                    (job_id, alignment, clustering_type, association_file, status, kill, requested_at) 
                    VALUES (%s, %s, %s, %s, %s, false, now())
                """)

                cur.execute(query, (self.job_id, self.alignment, 'default', None, 'waiting'))
                conn.commit()

    def cleanup(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(self.config.linkset_schema_name)))
            conn.commit()
