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
        jobs = []
        n1 = 0
        last_checked_downloading = None
        try:
            with db_conn() as conn:
                while True:
                    print('\rLooking for new job...', end='')

                    while len(jobs) < 1:
                        if not last_checked_downloading or time.time() - last_checked_downloading > 60:
                            include_downloading = "OR status = 'Downloading'"
                            last_checked_downloading = time.time()
                        else:
                            include_downloading = ''

                        with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                            sql_string = """
                                SELECT *
                                FROM reconciliation_jobs
                                WHERE status = 'Requested'
                                %s
                                ORDER BY requested_at""" % include_downloading

                            cur.execute(sql_string)

                            jobs = cur.fetchall()
                            conn.commit()

                            if len(jobs) < 1:
                                time.sleep(2)

                    found_new_requests = False
                    for job in jobs:
                        print('\rJob %s started.' % job['job_id'], end='')

                        process_start_time = str(datetime.datetime.now())
                        update_job_data(job['job_id'], {'status': 'Processing', 'processing_at': process_start_time})

                        with open('./rdf/%s_output.nq.gz' % job['job_id'], 'wb') as output_file:
                            with subprocess.Popen(['python', '/app/run_json.py', '-r', job['resources_filename'], '-m', job['mappings_filename']],
                                                  stdout=subprocess.PIPE) as converting_process:
                                subprocess.run(['gzip'], stdin=converting_process.stdout, stdout=output_file)

                        if converting_process.returncode == 0:
                            found_new_requests = True
                            print('\rJob %s finished.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'Finished', 'finished_at': str(datetime.datetime.now())})
                        elif converting_process.returncode == 3:
                            print('\rJob %s downloading.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'Downloading'})
                        else:
                            found_new_requests = True
                            print('\rJob %s failed.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'Failed'})

                    jobs = []

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n1 += 1
            time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))
