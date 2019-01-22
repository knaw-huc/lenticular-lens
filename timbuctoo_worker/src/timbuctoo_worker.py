from config_db import db_conn, run_query
from datasets_config import DatasetsConfig
import datetime
from psycopg2 import extras as psycopg2_extras
import psycopg2
import random
import time


if __name__ == '__main__':
    while True:
        job = None
        n1 = 0
        try:
            with db_conn() as conn:
                while True:
                    print('\rLooking for new Timbuctoo job...', end='')

                    while not job:
                        with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                            cur.execute("""
                                SELECT *
                                FROM timbuctoo_jobs
                                WHERE processing_at IS NULL
                                AND finished_at IS NULL
                                ORDER BY requested_at
                                LIMIT 1;""")

                            job = cur.fetchone()
                            conn.commit()

                            if not job:
                                time.sleep(2)

                    print('Job %s started.' % job['id'])

                    process_start_time = str(datetime.datetime.now())
                    run_query(
                        "UPDATE timbuctoo_jobs SET processing_at = %s WHERE id = %s",
                        (process_start_time, job['id'])
                    )

                    collection = DatasetsConfig().dataset(job['dataset_id']).collection(job['collection_id'])
                    collection.create_cached_view(job['limit'], False)

                    process_finish_time = str(datetime.datetime.now())
                    run_query(
                        "UPDATE timbuctoo_jobs SET finished_at = %s WHERE id = %s",
                        (process_finish_time, job['id'])
                    )

                    print('Job %s finished.' % job['id'])

                    job = None

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n1 += 1
            time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))
