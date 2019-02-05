import datetime
from helpers import update_job_data
import psycopg2
from psycopg2 import extras as psycopg2_extras
import subprocess
from config_db import db_conn
import pathlib
import random
import signal
import time


def teardown(signum=0, frame=None):
    print('Worker stopped.')

    if current_job:
        update_job_data(current_job['job_id'], {'status': current_job['status']})

    exit(signum)


if __name__ == '__main__':
    current_job = None

    signal.signal(signal.SIGTERM, teardown)

    pathlib.Path('rdf').mkdir(exist_ok=True)

    while True:
        jobs = []
        n1 = 0
        try:
            with db_conn() as conn:
                print('Looking for new job...')
                while True:

                    while len(jobs) < 1:

                        with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                            sql_string = """
                                SELECT *
                                FROM reconciliation_jobs
                                WHERE status = 'Requested'
                                OR status = 'Downloading'
                                ORDER BY requested_at"""

                            cur.execute(sql_string)

                            jobs = cur.fetchall()
                            conn.commit()

                            if len(jobs) < 1:
                                time.sleep(2)

                    found_new_requests = False
                    for job in jobs:
                        current_job = job

                        # Lock, check, update, commit
                        with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                            cur.execute("LOCK TABLE reconciliation_jobs IN ACCESS EXCLUSIVE MODE;")
                            cur.execute("SELECT status FROM reconciliation_jobs WHERE job_id = %s", (job['job_id'],))
                            if cur.fetchone()['status'] not in ['Requested', 'Downloading']:
                                conn.commit()
                                continue

                            print('Job %s started.' % job['job_id'])
                            process_start_time = str(datetime.datetime.now())
                            cur.execute(
                                """UPDATE reconciliation_jobs
                                SET status = 'Processing', processing_at = %s
                                WHERE job_id = %s""",
                                (process_start_time, job['job_id'])
                            )

                        conn.commit()

                        with open('./rdf/%s_output.nq.gz' % job['job_id'], 'wb') as output_file:
                            with subprocess.Popen(['python', '/app/run_json.py', '-r', job['resources_filename'], '-m', job['mappings_filename']],
                                                  stdout=subprocess.PIPE) as converting_process:
                                subprocess.run(['gzip'], stdin=converting_process.stdout, stdout=output_file)

                        if converting_process.returncode == 0:
                            found_new_requests = True
                            print('Job %s finished.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'Finished', 'finished_at': str(datetime.datetime.now())})
                        elif converting_process.returncode == 3:
                            print('Job %s downloading.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'Downloading'})
                        else:
                            found_new_requests = True
                            print('Job %s failed.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'Failed'})

                    if not found_new_requests:
                        time.sleep(2)
                    jobs = []

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n1 += 1
            time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))
