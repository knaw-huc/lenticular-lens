import datetime
import fcntl
import gzip
from helpers import update_job_data, table_to_csv
from linksets_collection import LinksetsCollection
import locale
import psycopg2
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
import subprocess
from config_db import db_conn
import os
from os.path import join
import pathlib
import random
import re
import signal
import time
from hashlib import md5

locale.setlocale(locale.LC_ALL, '')


def hasher(object):

    # h = blake2b(digest_size=10)
    # h.update(bytes(object.__str__(), encoding='utf-8'))
    # print(F"H{h.hexdigest()}")
    h = md5()
    h.update(bytes(object.__str__(), encoding='utf-8'))
    return F"H{h.hexdigest()[:15]}"


def non_block_peek(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        output_bytes = output.peek(1)
        return output_bytes
    except:
        return b""
    finally:
        fcntl.fcntl(fd, fcntl.F_SETFL, fl)


def teardown(signum=0, frame=None):
    print('Worker stopped.')

    if current_job:
        update_job_data(current_job['job_id'], {'status': current_job['status']})

    exit(signum)


if __name__ == '__main__':
    current_job = None
    found_new_requests = False

    signal.signal(signal.SIGTERM, teardown)

    pathlib.Path('rdf').mkdir(exist_ok=True)

    print('Looking for new job...')
    while True:
        jobs = []
        n1 = 0
        if found_new_requests:
            print('Looking for new job...')
        try:
            with db_conn() as conn:
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

                        with subprocess.Popen(['python', '/app/run_json.py', '-r', job['resources_filename'], '-m', job['mappings_filename']],
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as converting_process:
                            with open('/common/src/LLData/rdf/%s_output.nq.gz' % job['job_id'], 'wb') as output_file:
                                with subprocess.Popen(['gzip'], stdin=converting_process.stdout, stdout=output_file) as gzip_process:
                                    messages_log = ''
                                    for converting_output in converting_process.stderr:
                                        message = converting_output.decode('utf-8')
                                        print(message)
                                        messages_log += message + '\n'
                                        update_job_data(job['job_id'], {'status': message})
                                        if message.startswith('Generating linkset '):
                                            view_name = re.search(r'(?<=Generating linkset ).+(?=.$)', message)[0]
                                            next_out = None
                                            while not next_out:
                                                next_out = non_block_peek(converting_process.stderr)
                                                time.sleep(1)
                                                with db_conn() as conn1:
                                                    with conn1.cursor() as cur:
                                                        try:
                                                            cur.execute(psycopg2_sql.SQL('SELECT last_value FROM {}.{}').format(
                                                                psycopg2_sql.Identifier('job_' + job['job_id']),
                                                                psycopg2_sql.Identifier(view_name + '_count'),
                                                            ))
                                                        except psycopg2.ProgrammingError:
                                                            continue
                                                        inserted = cur.fetchone()[0]
                                                        conn1.commit()
                                                inserted_message = '%s links found so far.' % locale.format_string('%i', inserted, grouping=True)
                                                print(inserted_message)
                                                update_job_data(job['job_id'], {'status': inserted_message})

                        if converting_process.returncode == 0:
                            found_new_requests = True

                            print("Generating CSVs")
                            linksets_collection = LinksetsCollection(job['resources_filename'], job['mappings_filename'])
                            for match in linksets_collection.matches:
                                if match.is_association:
                                    from src.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR as CSV_DIR
                                    prefix = 'association'
                                else:
                                    from src.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR as CSV_DIR
                                    prefix = 'alignment'

                                today = datetime.date.isoformat(datetime.date.today()).replace('-', '')
                                # now = f"{today}_{re.findall('..:.*', str(datetime.datetime.now()))[0]}"
                                filename = f'{prefix}_{hasher(job["job_id"])}_{match.name_original}.csv.gz'

                                print('Creating file ' + join(CSV_DIR, filename))
                                with gzip.open(join(CSV_DIR, filename), 'wt') as csv_file:
                                    table_to_csv(f'job_{job["job_id"]}.{match.name}', csv_file)

                            print('Cleaning up.')
                            print('Dropping schema.')
                            with conn.cursor() as cur:
                                cur.execute(psycopg2_sql.SQL(
                                    'DROP SCHEMA {} CASCADE')
                                            .format(psycopg2_sql.Identifier(f'job_{job["job_id"]}')))
                                conn.commit()
                            print(f'Schema job_{job["job_id"]} dropped.')
                            print('Cleanup complete.')

                            print('Job %s finished.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'Finished', 'finished_at': str(datetime.datetime.now())})
                        elif converting_process.returncode == 3:
                            print('Job %s downloading.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'Downloading'})
                        else:
                            found_new_requests = True
                            print('Job %s failed.' % job['job_id'])
                            update_job_data(job['job_id'], {'status': 'FAILED: ' + messages_log})

                    if not found_new_requests:
                        time.sleep(2)
                    jobs = []

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n1 += 1
            time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))
