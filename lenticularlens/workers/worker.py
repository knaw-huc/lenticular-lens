import time
import random
import locale

from lenticularlens.util.config_db import conn_pool
from psycopg.rows import dict_row
from psycopg import InterfaceError, OperationalError

locale.setlocale(locale.LC_ALL, '')


class Worker:
    def __init__(self, table, watch_sql):
        self._table = table
        self._watch_sql = watch_sql
        self._job = None
        self._job_data = None
        self._killed = False

    def run(self):
        while not self._killed:
            try:
                with conn_pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("LOCK TABLE %s IN ACCESS EXCLUSIVE MODE;" % self._table)
                    cur.execute(self._watch_sql)

                    job_data = cur.fetchone()
                    if job_data:
                        self._job_data = job_data
                        self._update_status(cur)

                    conn.commit()

                if job_data:
                    self._run_job()
                else:
                    time.sleep(2)
            except (InterfaceError, OperationalError):
                time.sleep(random.randint(0, 1000) / 1000)

    def teardown(self):
        self._killed = True
        if self._job:
            self._job.kill()

    def _create_job(self):
        pass

    def _update_status(self, cur):
        pass

    def _run_job(self):
        self._create_job()
        self._job.run()
        self._cleanup()

    def _cleanup(self):
        self._job = None
        self._job_data = None
