import datetime
from helpers import update_job_data
import psycopg2
from psycopg2 import extras as psycopg2_extras
import subprocess
from config_db import db_conn
import pathlib
import random
import time


if __name__ == '__main__':
    pathlib.Path('rdf').mkdir(exist_ok=True)

    while True:
        job = None
        n1 = 0
        try:
            with db_conn() as conn:
                while True:
                    print('\rLooking for new job...', end='')

                    while not job:
                        with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                            cur.execute("""
                                SELECT *
                                FROM reconciliation_jobs
                                WHERE status = 'Requested'
                                ORDER BY requested_at
                                LIMIT 1;""")

                            job = cur.fetchone()

                            conn.commit()

                            if not job:
                                time.sleep(2)

                    print('\rJob %s started.' % job['job_id'], end='')

                    process_start_time = str(datetime.datetime.now())
                    update_job_data(job['job_id'], {'status': 'Processing', 'processing_at': process_start_time})

                    with open('./rdf/%s_output.nq.gz' % job['job_id'], 'wb') as output_file:
                        with subprocess.Popen(['python', '/app/run_json.py', '-r', job['resources_filename'], '-m', job['mappings_filename']],
                                              stdout=subprocess.PIPE) as converting_process:
                            blabla = subprocess.run(['gzip'], stdin=converting_process.stdout, stdout=output_file)

                    if converting_process.returncode == 0:
                        update_job_data(job['job_id'], {'status': 'Finished', 'finished_at': str(datetime.datetime.now())})
                    else:
                        update_job_data(job['job_id'], {'status': 'Failed'})

                    print('\rJob %s finished.' % job['job_id'])

                    job = None
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n1 += 1
            time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))
