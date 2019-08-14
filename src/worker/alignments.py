import os
import re
import time
import gzip
import fcntl
import locale
import datetime
import subprocess

from subprocess import PIPE
from os.path import join, dirname, realpath

from common.config_db import db_conn
from common.helpers import hasher, update_alignment_job, table_to_csv

from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR

from psycopg2 import sql as psycopg2_sql, ProgrammingError
from worker.matching.linksets_collection import LinksetsCollection


def run_alignment(job_id, alignment):
    with subprocess.Popen(['python', './matching/run_json.py', '--job-id', job_id, '--run-mapping', str(alignment)],
                          cwd=dirname(realpath(__file__)), stdout=PIPE, stderr=PIPE) as converting_process:
        messages_log = ''

        for converting_output in converting_process.stderr:
            message = converting_output.decode('utf-8')
            messages_log += message + '\n'

            print(message)
            update_alignment_job(job_id, alignment, {'status': message})

            if message.startswith('Generating linkset '):
                view_name = re.search(r'(?<=Generating linkset ).+(?=.$)', message)[0]
                next_out = None

                while not next_out:
                    next_out = non_block_peek(converting_process.stderr)
                    time.sleep(1)

                    with db_conn() as conn:
                        with conn.cursor() as cur:
                            try:
                                cur.execute(psycopg2_sql.SQL('SELECT last_value FROM {}.{}').format(
                                    psycopg2_sql.Identifier('job_' + job_id),
                                    psycopg2_sql.Identifier(view_name + '_count'),
                                ))
                            except ProgrammingError:
                                continue

                            inserted = cur.fetchone()[0]
                            conn.commit()

                    inserted_message = '%s links found so far.' \
                                       % locale.format_string('%i', inserted, grouping=True)
                    print(inserted_message)
                    update_alignment_job(job_id, alignment, {'status': inserted_message})

    if converting_process.returncode == 0:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}.{}').format(
                    psycopg2_sql.Identifier('job_' + job_id),
                    psycopg2_sql.Identifier(view_name)))
                inserted = cur.fetchone()[0]

            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE alignments SET links_count = %s WHERE job_id = %s AND alignment = %s",
                    (inserted, job_id, alignment))

        print("Generating CSVs")
        linksets_collection = LinksetsCollection(job_id=job_id)
        for match in linksets_collection.matches:
            if str(match.id) != str(alignment):
                continue

            columns = [psycopg2_sql.Identifier('source_uri'), psycopg2_sql.Identifier('target_uri')]
            if match.is_association:
                prefix = 'association'
            else:
                prefix = 'alignment'
                columns.append(psycopg2_sql.Identifier('__cluster_similarity'))

            filename = f'{prefix}_{hasher(job_id)}_alignment_{match.id}.csv.gz'

            print('Creating file ' + join(CSV_ASSOCIATIONS_DIR, filename))
            with gzip.open(join(CSV_ASSOCIATIONS_DIR, filename), 'wt') as csv_file:
                table_to_csv(f'job_{job_id}.{match.name}', columns, csv_file)

        print('Cleaning up.')
        print('Dropping schema.')

        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE').format(
                    psycopg2_sql.Identifier(f'job_{job_id}')))
                conn.commit()

        print(f'Schema job_{job_id} dropped.')
        print('Cleanup complete.')
        print('Job %s finished.' % job_id)

        update_alignment_job(job_id, alignment, {'status': 'Finished', 'finished_at': str(datetime.datetime.now())})
    elif converting_process.returncode == 3:
        print('Job %s downloading.' % job_id)
        update_alignment_job(job_id, alignment, {'status': 'Downloading'})
    else:
        print('Job %s failed.' % job_id)
        update_alignment_job(job_id, alignment, {'status': 'FAILED: ' + messages_log})


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
