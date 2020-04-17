import re
import time

from psycopg2 import sql as psycopg2_sql, ProgrammingError

from ll.job.data import Job
from ll.job.matching_sql import MatchingSql

from ll.worker.job import WorkerJob
from ll.util.config_db import db_conn


class LinksetJob(WorkerJob):
    def __init__(self, job_id, id):
        self._job_id = job_id
        self._id = id

        self._job = None
        self._matching_sql = None

        self.reset()
        super().__init__(self.run_generated_sql)

    def reset(self):
        self._job = Job(self._job_id)
        self._matching_sql = MatchingSql(self._job, self._id)

    def run(self):
        download_status_set = False
        while self._job.has_queued_entity_type_selections(self._id) and not self._killed:
            if not download_status_set:
                self._job.update_linkset(self._id, {'status': 'downloading'})
                download_status_set = True

            time.sleep(1)
            self.reset()

        super().run()

    def run_generated_sql(self):
        if not self._killed:
            self.process_sql(self._matching_sql.generate_schema_sql())

        if not self._killed:
            self._status = 'Generating entity-type selections'
            self.process_sql(self._matching_sql.generate_entity_type_selection_sql())

        if not self._killed:
            self._status = 'Generating source entities'
            self.process_sql(self._matching_sql.generate_match_source_sql())

        if not self._killed:
            self._status = 'Generating target entities'
            self.process_sql(self._matching_sql.generate_match_target_sql())

        if not self._killed:
            self._status = 'Generating indexes'
            self.process_sql(self._matching_sql.generate_match_index_sql())

        if not self._killed:
            self._status = 'Looking for links'
            self.process_sql(self._matching_sql.generate_match_linkset_sql())

    def process_sql(self, sql):
        sql_string = sql.as_string(self._db_conn)
        for statement in sql_string.split(';\n'):
            statement = statement.strip()

            if statement.startswith('--'):
                continue

            if re.search(r'\S', statement):
                if re.match(r'^\s*SELECT', statement) and not re.search(r'set_config\(', statement):
                    continue
                else:
                    with self._db_conn.cursor() as cur:
                        cur.execute(statement)
                        self._db_conn.commit()

    def watch_process(self):
        with db_conn() as conn, conn.cursor() as cur:
            data = {'status_message': self._status}

            for sequence_name in ('linkset_count', 'source_count', 'target_count'):
                try:
                    cur.execute(psycopg2_sql.SQL('SELECT is_called, last_value FROM {}.{}').format(
                        psycopg2_sql.Identifier(self._job.linkset_schema_name(self._id)),
                        psycopg2_sql.Identifier(sequence_name),
                    ))

                    seq = cur.fetchone()
                    is_called = seq[0]
                    if is_called:
                        inserted = seq[1]
                        if sequence_name == 'source_count':
                            data['sources_count'] = inserted
                        elif sequence_name == 'target_count':
                            data['targets_count'] = inserted
                        else:
                            data['links_count'] = inserted
                except ProgrammingError:
                    pass
                finally:
                    conn.commit()

        self._job.update_linkset(self._id, data)

    def watch_kill(self):
        linkset = self._job.linkset(self._id)
        if linkset['kill']:
            self.kill(reset=False)

    def on_kill(self, reset):
        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        self._job.update_linkset(self._id, job_data)

        self.cleanup()

    def on_exception(self):
        err_message = str(self._exception)
        self._job.update_linkset(self._id, {'status': 'failed', 'status_message': err_message})

        self.cleanup()

    def on_finish(self):
        self.watch_process()

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}').format(
                psycopg2_sql.Identifier(self._job.linkset_table_name(self._id))))
            links = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}.{}').format(
                psycopg2_sql.Identifier(self._job.linkset_schema_name(self._id)),
                psycopg2_sql.Identifier('source')))
            sources = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}.{}').format(
                psycopg2_sql.Identifier(self._job.linkset_schema_name(self._id)),
                psycopg2_sql.Identifier('target')))
            targets = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(self._job.linkset_schema_name(self._id))))

            cur.execute("UPDATE linksets "
                        "SET status = %s, status_message = null, distinct_links_count = %s, "
                        "distinct_sources_count = %s, distinct_targets_count = %s, finished_at = now() "
                        "WHERE job_id = %s AND spec_id = %s",
                        ('done', links, sources, targets, self._job_id, self._id))

            if links == 0:
                cur.execute(psycopg2_sql.SQL('DROP TABLE {} CASCADE')
                            .format(psycopg2_sql.Identifier(self._job.linkset_table_name(self._id))))
            else:
                cur.execute("SELECT * FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = 'linkset'",
                            (self._job_id, self._id))
                clustering = cur.fetchone()

                if clustering:
                    query = psycopg2_sql.SQL("""
                        UPDATE clusterings 
                        SET status = %s, kill = false, requested_at = now(), processing_at = null, finished_at = null
                        WHERE job_id = %s AND spec_id = %s AND spec_type = 'linkset'
                    """)

                    cur.execute(query, ('waiting', self._job_id, self._id))
                else:
                    query = psycopg2_sql.SQL("""
                        INSERT INTO clusterings 
                        (job_id, spec_id, spec_type, clustering_type, association_file, status, kill, requested_at) 
                        VALUES (%s, %s, 'linkset', %s, %s, %s, false, now())
                    """)

                    cur.execute(query, (self._job_id, self._id, 'default', None, 'waiting'))

    def cleanup(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(self._job.linkset_schema_name(self._id))))
