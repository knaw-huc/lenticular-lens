from psycopg2 import sql, extras

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
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql.SQL('''
                SELECT  (SELECT count(*) FROM lenses.{lens_table}) AS links,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT source_uri AS uri FROM lenses.{lens_table} 
                            WHERE link_order = 'source_target' OR link_order = 'both'
                            UNION ALL
                            SELECT target_uri AS uri FROM lenses.{lens_table} 
                            WHERE link_order = 'target_source' OR link_order = 'both'
                        ) AS uris) AS lens_sources,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT target_uri AS uri FROM lenses.{lens_table} 
                            WHERE link_order = 'source_target' OR link_order = 'both'
                            UNION ALL
                            SELECT source_uri AS uri FROM lenses.{lens_table} 
                            WHERE link_order = 'target_source' OR link_order = 'both'
                        ) AS uris) AS lens_targets,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT source_uri AS uri FROM lenses.{lens_table} 
                            UNION ALL
                            SELECT target_uri AS uri FROM lenses.{lens_table}
                        ) AS uris) AS lens_entities
            ''').format(lens_table=sql.Identifier(self._job.table_name(self._id))))

            result = cur.fetchone()
            cur.execute("UPDATE lenses "
                        "SET status = %s, status_message = null, links_count = %s, "
                        "lens_sources_count = %s, lens_targets_count = %s, lens_entities_count = %s, "
                        "finished_at = now() "
                        "WHERE job_id = %s AND spec_id = %s",
                        ('done', result['links'], result['lens_sources'], result['lens_targets'],
                         result['lens_entities'], self._job_id, self._id))

            if result['links'] == 0:
                cur.execute(sql.SQL('DROP TABLE lenses.{} CASCADE')
                            .format(sql.Identifier(self._job.table_name(self._id))))
            else:
                cur.execute("SELECT * FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = 'lens'",
                            (self._job_id, self._id))
                clustering = cur.fetchone()

                query = """
                    UPDATE clusterings 
                    SET status = 'waiting', kill = false, requested_at = now(), processing_at = null, finished_at = null
                    WHERE job_id = %s AND spec_id = %s AND spec_type = 'lens'
                """ if clustering else """
                    INSERT INTO clusterings 
                    (job_id, spec_id, spec_type, clustering_type, status, kill, requested_at) 
                    VALUES (%s, %s, 'lens', 'default', 'waiting', false, now())
                """

                cur.execute(query, (self._job_id, self._id))
