import os
import sys
import time
import random
import locale
import signal

from enum import Enum

from ll.util.config_db import conn_pool
from ll.util.config_logging import config_logger

from ll.worker.timbuctoo import TimbuctooJob
from ll.worker.linkset import LinksetJob
from ll.worker.lens import LensJob
from ll.worker.clustering import ClusteringJob
from ll.worker.reconciliation import ReconciliationJob

from psycopg.rows import dict_row
from psycopg import InterfaceError, OperationalError

locale.setlocale(locale.LC_ALL, '')


class WorkerType(Enum):
    TIMBUCTOO = 'timbuctoo'
    LINKSET = 'linkset'
    LENS = 'lens'
    CLUSTERING = 'clustering'
    RECONCILIATION = 'reconciliation'


class Worker:
    def __init__(self, type):
        self._type = type
        self._job = None
        self._job_data = None
        self._killed = False

    def teardown(self):
        self._killed = True
        if self._job:
            self._job.kill()

    def run(self):
        if self._type == WorkerType.TIMBUCTOO:
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
                WHERE "table_name" = %s""", (self._job_data['table_name'],))

            self.watch_for_jobs("timbuctoo_tables", watch_query, update_status, self.run_timbuctoo_job)
        elif self._type == WorkerType.LINKSET:
            watch_query = """
                SELECT *
                FROM linksets ls
                WHERE ls.status = 'waiting'
                ORDER BY ls.requested_at
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE linksets
                SET status = 'running', processing_at = now()
                WHERE job_id = %s AND spec_id = %s""", (self._job_data['job_id'], self._job_data['spec_id']))

            self.watch_for_jobs("linksets", watch_query, update_status, self.run_linkset_job)
        elif self._type == WorkerType.LENS:
            watch_query = """
                SELECT *
                FROM lenses ls
                WHERE ls.status = 'waiting'
                ORDER BY ls.requested_at
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE lenses
                SET status = 'running', processing_at = now()
                WHERE job_id = %s AND spec_id = %s""", (self._job_data['job_id'], self._job_data['spec_id']))

            self.watch_for_jobs("lenses", watch_query, update_status, self.run_lens_job)
        elif self._type == WorkerType.CLUSTERING:
            watch_query = """
                SELECT *
                FROM clusterings cl
                WHERE cl.status = 'waiting'
                ORDER BY cl.requested_at
                LIMIT 1
            """

            update_status = lambda cur: cur.execute("""
                UPDATE clusterings
                SET status = 'running', processing_at = now()
                WHERE job_id = %s AND spec_id = %s AND spec_type = %s
            """, (self._job_data['job_id'], self._job_data['spec_id'], self._job_data['spec_type']))

            self.watch_for_jobs("clusterings", watch_query, update_status, self.run_clustering_job)
        elif self._type == WorkerType.RECONCILIATION:
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
                WHERE job_id = %s AND spec_id = %s AND spec_type = %s
            """, (self._job_data['job_id'], self._job_data['spec_id'], self._job_data['spec_type']))

            self.watch_for_jobs("clusterings", watch_query, update_status, self.run_reconciliation_job)

    def watch_for_jobs(self, table, watch_sql, update_status, run_job):
        while not self._killed:
            try:
                with conn_pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("LOCK TABLE %s IN ACCESS EXCLUSIVE MODE;" % table)
                    cur.execute(watch_sql)

                    job_data = cur.fetchone()
                    if job_data:
                        self._job_data = job_data
                        update_status(cur)

                    conn.commit()

                if job_data:
                    run_job()
                else:
                    time.sleep(2)
            except (InterfaceError, OperationalError):
                time.sleep(random.randint(0, 1000) / 1000)

    def run_timbuctoo_job(self):
        self._job = TimbuctooJob(table_name=self._job_data['table_name'],
                                 graphql_endpoint=self._job_data['graphql_endpoint'],
                                 dataset_id=self._job_data['dataset_id'],
                                 collection_id=self._job_data['collection_id'],
                                 prefix_mappings=self._job_data['prefix_mappings'],
                                 columns=self._job_data['columns'],
                                 cursor=self._job_data['next_page'],
                                 rows_count=self._job_data['rows_count'],
                                 rows_per_page=1000)
        self._job.run()
        self.cleanup()

    def run_linkset_job(self):
        self._job = LinksetJob(job_id=self._job_data['job_id'], id=self._job_data['spec_id'])
        self._job.run()
        self.cleanup()

    def run_lens_job(self):
        self._job = LensJob(job_id=self._job_data['job_id'], id=self._job_data['spec_id'])
        self._job.run()
        self.cleanup()

    def run_clustering_job(self):
        self._job = ClusteringJob(job_id=self._job_data['job_id'], id=self._job_data['spec_id'],
                                  type=self._job_data['spec_type'])
        self._job.run()
        self.cleanup()

    def run_reconciliation_job(self):
        self._job = ReconciliationJob(job_id=self._job_data['job_id'], id=self._job_data['spec_id'],
                                      type=self._job_data['spec_type'])
        self._job.run()
        self.cleanup()

    def cleanup(self):
        self._job = None
        self._job_data = None


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
