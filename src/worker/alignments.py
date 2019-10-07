import re
import time
import locale
import datetime
import threading

from common.config_db import db_conn
from common.job_alignment import update_alignment_job

from psycopg2 import sql as psycopg2_sql, ProgrammingError
from worker.matching.linksets_collection import LinksetsCollection


class AlignmentJob:
    def __init__(self, job_id, alignment, status):
        self.job_id = job_id
        self.alignment = alignment
        self.status = status
        self.linksets_collection = LinksetsCollection(job_id=job_id, run_match=alignment)

    def run(self):
        thread = threading.Thread(target=self.linksets_collection.run)
        thread.start()

        while thread.is_alive():
            self.watch_process()
            time.sleep(1)

        if self.linksets_collection.has_queued_view:
            print('Job %s downloading.' % self.job_id)
            update_alignment_job(self.job_id, self.alignment, {'status': 'Downloading'})
        elif self.linksets_collection.exception:
            print('Job %s failed.' % self.job_id)
            err_message = str(self.linksets_collection.exception)
            update_alignment_job(self.job_id, self.alignment, {'status': 'FAILED: ' + err_message})
        else:
            self.finish()

    def kill(self):
        update_alignment_job(self.job_id, self.alignment, {'status': self.status})

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(f'job_{self.alignment}_{self.job_id}')))
            conn.commit()

    def watch_process(self):
        message = self.linksets_collection.status
        if not message:
            return

        if message.startswith('Generating linkset '):
            view_name = re.search(r'(?<=Generating linkset ).+(?=.$)', message)[0]

            with db_conn() as conn, conn.cursor() as cur:
                try:
                    cur.execute(psycopg2_sql.SQL('SELECT last_value FROM {}.{}').format(
                        psycopg2_sql.Identifier('job_' + str(self.alignment) + '_' + self.job_id),
                        psycopg2_sql.Identifier(view_name + '_count'),
                    ))
                except ProgrammingError:
                    return

                inserted = cur.fetchone()[0]
                conn.commit()

            if view_name.endswith('_source'):
                set = 'sources'
            elif view_name.endswith('_target'):
                set = 'sources'
            else:
                set = 'links'

            print('%s %s found so far.' % (locale.format_string('%i', inserted, grouping=True), set))
            update_alignment_job(self.job_id, self.alignment, {set + '_count': inserted, 'status': message})
        else:
            print(message)
            update_alignment_job(self.job_id, self.alignment, {'status': message})

    def finish(self):
        with db_conn() as conn:
            with conn.cursor() as cur:
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

                cur.execute("UPDATE alignments SET links_count = %s, sources_count = %s, targets_count = %s "
                            "WHERE job_id = %s AND alignment = %s",
                            (links, sources, targets, self.job_id, self.alignment))
                conn.commit()

            print('Start clustering.')

            with conn.cursor() as cur:
                cur.execute('SELECT * FROM clusterings WHERE job_id = %s AND alignment = %s',
                            (self.job_id, self.alignment))
                clustering = cur.fetchone()

                if clustering:
                    query = psycopg2_sql.SQL("""
                        UPDATE clusterings 
                        SET status = %s, requested_at = now(), processing_at = null, finished_at = null
                        WHERE job_id = %s AND alignment = %s
                    """)

                    cur.execute(query, ('Requested', self.job_id, self.alignment))
                    conn.commit()
                else:
                    query = psycopg2_sql.SQL("""
                        INSERT INTO clusterings 
                        (job_id, alignment, clustering_type, association_file, status, requested_at) 
                        VALUES (%s, %s, %s, %s, %s, now())
                    """)

                    cur.execute(query, (self.job_id, self.alignment, 'default', None, 'Requested'))
                    conn.commit()

            print('Clustering job sent.')
            print('Cleaning up.')
            print('Dropping schema.')

            with conn.cursor() as cur:
                cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                            .format(psycopg2_sql.Identifier(f'job_{str(self.alignment)}_{self.job_id}')))
                conn.commit()

        print(f'Schema job_{str(self.alignment)}_{self.job_id} dropped.')
        print('Cleanup complete.')
        print(f'Job {self.job_id} for alignment {str(self.alignment)} finished.')

        update_alignment_job(self.job_id, self.alignment,
                             {'status': 'Finished', 'finished_at': str(datetime.datetime.now())})
