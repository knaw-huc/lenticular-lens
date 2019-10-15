import time
import threading

from common.config_db import db_conn
from common.job_alignment import get_job_alignment, update_alignment_job

from psycopg2 import sql as psycopg2_sql, ProgrammingError
from worker.matching.linksets_collection import LinksetsCollection


class AlignmentJob:
    def __init__(self, job_id, alignment):
        self.job_id = job_id
        self.alignment = alignment

        self.killed = False
        self.linksets_collection = LinksetsCollection(job_id=job_id, run_match=alignment)

    def run(self):
        thread = threading.Thread(target=self.linksets_collection.run)
        thread.start()

        while not self.killed and thread.is_alive():
            self.watch_process_counts()
            self.watch_kill()
            time.sleep(1)

        if self.killed:
            return

        if self.linksets_collection.has_queued_view:
            print('Job %s downloading.' % self.job_id)
            update_alignment_job(self.job_id, self.alignment, {'status': 'downloading'})
            self.cleanup()
        elif self.linksets_collection.exception:
            print('Job %s failed.' % self.job_id)
            err_message = str(self.linksets_collection.exception)
            update_alignment_job(self.job_id, self.alignment, {'status': 'failed', 'failed_message': err_message})
            self.cleanup()
        else:
            self.finish()

    def kill(self, reset=True):
        self.killed = True

        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'failed_message': 'Killed manually'}
        update_alignment_job(self.job_id, self.alignment, job_data)

        self.cleanup()

    def watch_process_counts(self):
        with db_conn() as conn, conn.cursor() as cur:
            counts = {}
            for suffix in ('_count', '_source_count', '_target_count'):
                sequence_name = self.linksets_collection.view_name + suffix

                try:
                    cur.execute(psycopg2_sql.SQL('SELECT last_value FROM {}.{}').format(
                        psycopg2_sql.Identifier('job_' + str(self.alignment) + '_' + self.job_id),
                        psycopg2_sql.Identifier(sequence_name),
                    ))
                except ProgrammingError:
                    return

                inserted = cur.fetchone()[0]
                conn.commit()

                if suffix == '_source_count':
                    counts['sources_count'] = inserted
                elif suffix == '_target_count':
                    counts['targets_count'] = inserted
                else:
                    counts['links_count'] = inserted

        update_alignment_job(self.job_id, self.alignment, counts)

    def watch_kill(self):
        alignment_job = get_job_alignment(self.job_id, self.alignment)
        if alignment_job['kill']:
            self.kill(reset=False)

    def finish(self):
        self.watch_process_counts()

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}').format(
                psycopg2_sql.Identifier('linkset_' + self.job_id + '_' + str(self.alignment))))
            links = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}.{}').format(
                psycopg2_sql.Identifier('job_' + str(self.alignment) + '_' + self.job_id),
                psycopg2_sql.Identifier(self.linksets_collection.view_name + '_source')))
            sources = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}.{}').format(
                psycopg2_sql.Identifier('job_' + str(self.alignment) + '_' + self.job_id),
                psycopg2_sql.Identifier(self.linksets_collection.view_name + '_target')))
            targets = cur.fetchone()[0]

            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(f'job_{str(self.alignment)}_{self.job_id}')))

            cur.execute("UPDATE alignments "
                        "SET status = %s, distinct_links_count = %s, "
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
                        .format(psycopg2_sql.Identifier(f'job_{self.alignment}_{self.job_id}')))
            conn.commit()
