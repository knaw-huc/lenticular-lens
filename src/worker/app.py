import os
import time
import random
import locale
import signal

from enum import Enum

from common.config_db import db_conn
from common.helpers import update_alignment_job, update_clustering_job

from worker.timbuctoo import download_from_timbuctoo
from worker.alignments import run_alignment
from worker.clustering import start_clustering

from psycopg2 import extras as psycopg2_extras, InterfaceError, OperationalError

locale.setlocale(locale.LC_ALL, '')


class WorkerType(Enum):
    TIMBUCTOO = 'timbuctoo'
    ALIGNMENTS = 'alignments'
    CLUSTERINGS = 'clusterings'


class Worker:
    def __init__(self, type):
        self.job = None
        self.type = type

    def teardown(self):
        print('Worker %s stopped.' % str(self.type))

        if self.job:
            if self.type == WorkerType.ALIGNMENTS:
                update_alignment_job(self.job['job_id'], self.job['alignment'], {'status': self.job['status']})
            elif self.type == WorkerType.CLUSTERINGS:
                update_clustering_job(self.job['job_id'], self.job['alignment'], {'status': self.job['status']})

    def run(self):
        if self.type == WorkerType.TIMBUCTOO:
            watch_query = """
                SELECT *
                FROM timbuctoo_tables
                WHERE update_start_time IS NULL
                OR (
                    (update_finish_time IS NULL OR update_finish_time < update_start_time)
                    AND update_start_time < now() - interval '2 minutes'
                    AND (last_push_time IS NULL OR last_push_time < now() - interval '2 minutes')
                )
                ORDER BY create_time
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE timbuctoo_tables 
                SET update_start_time = now() 
                WHERE "table_name" = %s""", (self.job['table_name'],))

            self.watch_for_jobs("timbuctoo_tables", watch_query, update_status, self.run_timbuctoo_job)
        elif self.type == WorkerType.ALIGNMENTS:
            watch_query = """
                SELECT *
                FROM alignments aj
                JOIN reconciliation_jobs rj ON aj.job_id = rj.job_id
                WHERE aj.status = 'Requested' OR aj.status = 'Downloading'
                ORDER BY aj.requested_at
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE alignments
                SET status = 'Processing', processing_at = now()
                WHERE job_id = %s AND alignment = %s""", (self.job['job_id'], self.job['alignment']))

            self.watch_for_jobs("alignments", watch_query, update_status, self.run_alignment_job)
        elif self.type == WorkerType.CLUSTERINGS:
            watch_query = """
                SELECT *
                FROM clusterings cl
                WHERE cl.status = 'Requested'
                ORDER BY cl.requested_at
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE clusterings
                SET status = 'Processing', processing_at = now()
                WHERE job_id = %s AND alignment = %s""", (self.job['job_id'], self.job['alignment']))

            self.watch_for_jobs("clusterings", watch_query, update_status, self.run_clustering_job)

    def watch_for_jobs(self, table, watch_sql, update_status, run_job):
        n1 = 0
        while True:
            try:
                with db_conn() as conn, conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                    cur.execute("LOCK TABLE %s IN ACCESS EXCLUSIVE MODE;" % table)
                    cur.execute(watch_sql)

                    job = cur.fetchone()
                    if job:
                        self.job = job
                        update_status(cur)

                    conn.commit()

                if job:
                    run_job()
                else:
                    time.sleep(2)
            except (InterfaceError, OperationalError):
                n1 += 1
                time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))

    def run_timbuctoo_job(self):
        download_from_timbuctoo(
            table_name=self.job['table_name'],
            dataset_id=self.job['dataset_id'],
            collection_id=self.job['collection_id'],
            columns=self.job['columns'],
            cursor=self.job['next_page'],
            rows_count=self.job['rows_count'],
            rows_per_page=500
        )

    def run_alignment_job(self):
        run_alignment(
            job_id=self.job['job_id'],
            alignment=self.job['alignment']
        )

    def run_clustering_job(self):
        start_clustering(
            job_id=self.job['job_id'],
            alignment=self.job['alignment'],
            association_file=self.job['association_file'],
            clustering_id=self.job['clustering_id'],
        )


if __name__ == '__main__':
    def teardown(signum=0):
        worker.teardown()
        exit(signum)

    worker_type = WorkerType[os.environ['WORKER_TYPE'].upper()]
    worker = Worker(worker_type)
    signal.signal(signal.SIGTERM, teardown)
    worker.run()
