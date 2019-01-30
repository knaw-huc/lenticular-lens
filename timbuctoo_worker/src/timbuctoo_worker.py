import concurrent.futures
from config_db import db_conn, run_query
from datasets_config import DatasetsConfig
import datetime
from psycopg2 import extras as psycopg2_extras
import psycopg2
import random
import signal
import time


def reset_job():
    if job:
        print('Trying to reset job...')

        rt = 0
        while True:
            try:
                with db_conn() as conn:
                    with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                        cur.execute(
                            "UPDATE timbuctoo_jobs SET processing_at = NULL WHERE id = %s",
                            (job['id'], )
                        )
                    conn.commit()

            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                rt += 1
                print('Database error. Waiting...')
                time.sleep(0.5 + (random.randint(0, 1000) / 1000))
                print('Retry %i...' % rt)
                continue
            else:
                print('Job reset.')
                return


def teardown(signum=0, frame=None):
    print('Stopping Timbuctoo worker.')

    reset_job()

    exit(signum)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, teardown)

    job = None
    n1 = 0

    while True:
        try:
            with db_conn() as conn:
                print('Looking for new Timbuctoo job...')

                # By not setting job = None here, job will be retried after exception
                while not job:
                    with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                        cur.execute("LOCK TABLE timbuctoo_jobs IN ACCESS EXCLUSIVE MODE;")
                        cur.execute("""
                            SELECT *
                            FROM timbuctoo_jobs
                            WHERE processing_at IS NULL
                            AND finished_at IS NULL
                            ORDER BY requested_at
                            LIMIT 1;""")

                        job = cur.fetchone()
                        n1 = 0

                        if not job:
                            conn.commit()
                            time.sleep(2)

                print('Job %s started.' % job['id'])

                process_start_time = str(datetime.datetime.now())
                with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                    cur.execute(
                        "UPDATE timbuctoo_jobs SET processing_at = %s WHERE id = %s",
                        (process_start_time, job['id'])
                    )
                conn.commit()
                n1 = 0

                collection = DatasetsConfig().dataset(job['dataset_id']).collection(job['collection_id'])
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = [executor.submit(collection.create_cached_view, job['limit'], False)]
                    for completed_future in concurrent.futures.as_completed(future):
                        completed_future.result()

                process_finish_time = str(datetime.datetime.now())
                run_query(
                    "UPDATE timbuctoo_jobs SET finished_at = %s WHERE id = %s",
                    (process_finish_time, job['id'])
                )

                print('Job %s finished.' % job['id'])

                job = None
                n1 = 0

        except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            n1 += 1
            print('Database error: %s' % e)
            print('Waiting to retry...')
            time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))
            print('Retry %i...' % n1)

            continue
