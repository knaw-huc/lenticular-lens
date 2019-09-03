import re
import time
import random
import datetime
import psycopg2

from hashlib import md5
from os import listdir
from os.path import join, isfile, dirname, realpath

from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
from psycopg2.extensions import AsIs

from common.config_db import db_conn, execute_query, run_query
from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR


def hasher(object):
    h = md5()
    h.update(bytes(object.__str__(), encoding='utf-8'))
    return F"H{h.hexdigest()[:15]}"


def file_date():
    today = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    return f"{today}_{re.findall('..:.*', str(datetime.datetime.now()))[0]}"


def table_to_csv(table_name, columns, file):
    table_name = [psycopg2_sql.Identifier(name_part) for name_part in table_name.split('.')]

    with db_conn() as conn, conn.cursor() as cur:
        sql = cur.mogrify(
            psycopg2_sql.SQL("COPY (SELECT {columns} FROM {schema}.{table}) TO STDOUT WITH CSV DELIMITER ','")
                .format(columns=psycopg2_sql.SQL(', ').join(columns), schema=table_name[0], table=table_name[1]))
        cur.copy_expert(sql, file)


def get_json_from_file(filename):
    import jstyleson

    json_file = open(join(dirname(realpath(__file__)), 'json', filename), 'r')
    json_config = jstyleson.load(json_file)
    json_file.close()

    return json_config


def get_string_from_sql(sql):
    conn = db_conn()
    sql_string = sql.as_string(conn)
    conn.close()

    return sql_string


def hash_string(to_hash):
    return md5(to_hash.encode('utf-8')).hexdigest()


def get_job_data(job_id):
    n = 0
    while True:
        try:
            conn = db_conn()
            with conn:
                with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                    cur.execute('SELECT * FROM reconciliation_jobs WHERE job_id = %s', (job_id,))
                    job_data = cur.fetchone()
            break
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))

    return job_data


def get_job_alignments(job_id):
    return execute_query({
        'query': "SELECT * FROM alignments WHERE job_id = %s",
        'parameters': (job_id,)
    }, {'cursor_factory': psycopg2_extras.RealDictCursor})


def get_job_clusterings(job_id):
    n = 0
    while True:
        try:
            conn = db_conn()
            with conn:
                with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                    cur.execute('SELECT * FROM clusterings WHERE job_id = %s', (job_id,))
                    clusterings = cur.fetchall()
            break
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))

    return clusterings


def get_association_files():
    return [f for f in listdir(CSV_ASSOCIATIONS_DIR)
            if isfile(join(CSV_ASSOCIATIONS_DIR, f)) and f.endswith(('.csv', '.csv.gz'))]


def update_alignment_job(job_id, alignment, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    psycopg2_sql.SQL("UPDATE alignments SET ({}) = ROW %s WHERE job_id = %s AND alignment = %s")
                        .format(psycopg2_sql.SQL(', '.join(job_data.keys()))),
                    (tuple(job_data.values()), job_id, alignment))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break


def update_clustering_job(job_id, alignment, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        psycopg2_sql.SQL("UPDATE clusterings SET ({}) = ROW %s WHERE job_id = %s AND alignment = %s")
                            .format(
                            psycopg2_sql.SQL(', '.join(job_data.keys()))),
                        (tuple(job_data.values()), job_id, alignment))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break


def update_job_data(job_id, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn:
                with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                    if run_query('SELECT 1 FROM reconciliation_jobs WHERE job_id = %s', (job_id,)):
                        query = psycopg2_sql.SQL(
                            "UPDATE reconciliation_jobs SET ({}) = ROW %s, updated_at = NOW() WHERE job_id = %s"
                        ).format(psycopg2_sql.SQL(', '.join(job_data.keys())))
                        cur.execute(query, (tuple(job_data.values()), job_id))
                    else:
                        cur.execute(psycopg2_sql.SQL("INSERT INTO reconciliation_jobs (job_id, %s) VALUES %s"),
                                    (AsIs(', '.join(job_data.keys())), tuple([job_id] + list(job_data.values()))))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break
