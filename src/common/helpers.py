import re
import datetime

from hashlib import md5
from os import listdir
from os.path import join, isfile, dirname, realpath

from psycopg2 import sql as psycopg2_sql

from common.config_db import db_conn


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


def get_pagination_sql(limit=None, offset=0):
    return ('LIMIT ' + str(limit) + ' ' if limit else '') + ('OFFSET ' + str(offset) if offset > 0 else '')


def get_association_files():
    return []
