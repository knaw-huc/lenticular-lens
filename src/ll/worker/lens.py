from psycopg2 import sql as psycopg2_sql

from ll.job.job import Job
from ll.job.lens_sql import LensSql

from ll.worker.job import WorkerJob
from ll.util.config_db import db_conn


class LensJob(WorkerJob):
    def __init__(self, job_id, id):
        self._job_id = job_id
        self._id = id
        self._job = Job(job_id)

        super().__init__(self.generate_lens)

    def generate_lens(self):
        lens_sql = LensSql(self._job, self._id)
        if not self._killed:
            self._status = 'Generating lens'
            with self._db_conn.cursor() as cur:
                cur.execute(lens_sql.generate_lens_sql())
                self._db_conn.commit()

        if not self._killed:
            self._status = 'Finishing'
            with self._db_conn.cursor() as cur:
                cur.execute(lens_sql.generate_lens_finish_sql())
                self._db_conn.commit()

    def watch_process(self):
        pass

    def watch_kill(self):
        lens = self._job.lens(self._id)
        if lens['kill']:
            self.kill(reset=False)

    def on_kill(self, reset):
        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        self._job.update_lens(self._id, job_data)

    def on_exception(self):
        err_message = str(self._exception)
        self._job.update_lens(self._id, {'status': 'failed', 'status_message': err_message})

    def on_finish(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('''
                SELECT  (SELECT count(*) FROM lenses.{lens_table}) AS links_count,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT source_uri AS uri FROM lenses.{lens_table} 
                            WHERE link_order = 'source_target' OR link_order = 'both'
                            UNION ALL
                            SELECT target_uri AS uri FROM lenses.{lens_table} 
                            WHERE link_order = 'target_source' OR link_order = 'both'
                        ) AS uris) AS lens_sources_count,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT target_uri AS uri FROM lenses.{lens_table} 
                            WHERE link_order = 'source_target' OR link_order = 'both'
                            UNION ALL
                            SELECT source_uri AS uri FROM lenses.{lens_table} 
                            WHERE link_order = 'target_source' OR link_order = 'both'
                        ) AS uris) AS lens_targets_count
            ''').format(lens_table=psycopg2_sql.Identifier(self._job.table_name(self._id))))

            result = cur.fetchone()

            links = result[0]
            lens_sources_count = result[1]
            lens_targets_count = result[2]

            cur.execute("UPDATE lenses "
                        "SET status = %s, status_message = null, distinct_links_count = %s, "
                        "distinct_lens_sources_count = %s, distinct_lens_targets_count = %s, finished_at = now() "
                        "WHERE job_id = %s AND spec_id = %s",
                        ('done', links, lens_sources_count, lens_targets_count, self._job_id, self._id))

            if links == 0:
                cur.execute(psycopg2_sql.SQL('DROP TABLE lenses.{} CASCADE')
                            .format(psycopg2_sql.Identifier(self._job.table_name(self._id))))
            else:
                cur.execute("SELECT * FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = 'lens'",
                            (self._job_id, self._id))
                clustering = cur.fetchone()

                if clustering:
                    query = psycopg2_sql.SQL("""
                        UPDATE clusterings 
                        SET status = %s, kill = false, requested_at = now(), processing_at = null, finished_at = null
                        WHERE job_id = %s AND spec_id = %s AND spec_type = 'lens'
                    """)

                    cur.execute(query, ('waiting', self._job_id, self._id))
                else:
                    query = psycopg2_sql.SQL("""
                        INSERT INTO clusterings 
                        (job_id, spec_id, spec_type, clustering_type, association_file, status, kill, requested_at) 
                        VALUES (%s, %s, 'lens', %s, %s, %s, false, now())
                    """)

                    cur.execute(query, (self._job_id, self._id, 'default', None, 'waiting'))
