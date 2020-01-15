import os
import sys
import time
import random
import locale
import signal

from enum import Enum

from ll.util.config_db import db_conn
from ll.util.logging import config_logger

from ll.worker.timbuctoo import TimbuctooJob
from ll.worker.alignment import AlignmentJob
from ll.worker.clustering import ClusteringJob
from ll.worker.reconciliation import ReconciliationJob

from psycopg2 import extras as psycopg2_extras, InterfaceError, OperationalError

locale.setlocale(locale.LC_ALL, '')


class WorkerType(Enum):
    TIMBUCTOO = 'timbuctoo'
    ALIGNMENT = 'alignment'
    CLUSTERING = 'clustering'
    RECONCILIATION = 'reconciliation'


class Worker:
    def __init__(self, type):
        self.type = type
        self.job = None
        self.job_data = None

    def teardown(self):
        print('Worker %s stopped.' % str(self.type))

        if self.job:
            self.job.kill()

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
                WHERE "table_name" = %s""", (self.job_data['table_name'],))

            self.watch_for_jobs("timbuctoo_tables", watch_query, update_status, self.run_timbuctoo_job)
        elif self.type == WorkerType.ALIGNMENT:
            watch_query = """
                SELECT *
                FROM alignments aj
                JOIN reconciliation_jobs rj ON aj.job_id = rj.job_id
                WHERE aj.status = 'waiting' OR aj.status = 'downloading'
                ORDER BY aj.requested_at
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE alignments
                SET status = 'running', processing_at = now()
                WHERE job_id = %s AND alignment = %s""", (self.job_data['job_id'], self.job_data['alignment']))

            self.watch_for_jobs("alignments", watch_query, update_status, self.run_alignment_job)
        elif self.type == WorkerType.CLUSTERING:
            watch_query = """
                SELECT *
                FROM clusterings cl
                WHERE cl.status = 'waiting' AND (cl.association_file IS NULL OR cl.association_file = '')
                ORDER BY cl.requested_at
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE clusterings
                SET status = 'running', processing_at = now()
                WHERE job_id = %s AND alignment = %s""", (self.job_data['job_id'], self.job_data['alignment']))

            self.watch_for_jobs("clusterings", watch_query, update_status, self.run_clustering_job)
        elif self.type == WorkerType.RECONCILIATION:
            watch_query = """
                SELECT *
                FROM clusterings cl
                WHERE cl.status = 'waiting' AND cl.association_file IS NOT NULL AND cl.association_file != ''
                ORDER BY cl.requested_at
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE clusterings
                SET status = 'running', processing_at = now()
                WHERE job_id = %s AND alignment = %s""", (self.job_data['job_id'], self.job_data['alignment']))

            self.watch_for_jobs("clusterings", watch_query, update_status, self.run_reconciliation_job)

    def watch_for_jobs(self, table, watch_sql, update_status, run_job):
        while True:
            try:
                with db_conn() as conn, conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                    cur.execute("LOCK TABLE %s IN ACCESS EXCLUSIVE MODE;" % table)
                    cur.execute(watch_sql)

                    job_data = cur.fetchone()
                    if job_data:
                        self.job_data = job_data
                        update_status(cur)

                    conn.commit()

                if job_data:
                    run_job()
                else:
                    time.sleep(2)
            except (InterfaceError, OperationalError):
                time.sleep(random.randint(0, 1000) / 1000)

    def run_timbuctoo_job(self):
        self.job = TimbuctooJob(table_name=self.job_data['table_name'],
                                graphql_endpoint=self.job_data['graphql_endpoint'],
                                hsid=self.job_data['hsid'],
                                dataset_id=self.job_data['dataset_id'],
                                collection_id=self.job_data['collection_id'],
                                columns=self.job_data['columns'],
                                cursor=self.job_data['next_page'],
                                rows_count=self.job_data['rows_count'],
                                rows_per_page=500)
        self.job.run()
        self.cleanup()

    def run_alignment_job(self):
        self.job = AlignmentJob(job_id=self.job_data['job_id'], alignment=self.job_data['alignment'])
        self.job.run()
        self.cleanup()

    def run_clustering_job(self):
        self.job = ClusteringJob(job_id=self.job_data['job_id'], alignment=self.job_data['alignment'])
        self.job.run()
        self.cleanup()

    def run_reconciliation_job(self):
        self.job = ReconciliationJob(job_id=self.job_data['job_id'], alignment=self.job_data['alignment'],
                                     association_file=self.job_data['association_file'])
        self.job.run()
        self.cleanup()

    def cleanup(self):
        self.job = None
        self.job_data = None


if __name__ == '__main__':
    def teardown(signum=0):
        worker.teardown()
        sys.exit(signum)


    config_logger()

    worker_type = WorkerType[os.environ['WORKER_TYPE'].upper()]
    worker = Worker(worker_type)

    signal.signal(signal.SIGTERM, teardown)
    signal.signal(signal.SIGINT, teardown)

    worker.run()
