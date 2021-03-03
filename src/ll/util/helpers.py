import re
import datetime
import jstyleson

from psycopg2 import sql as psycopg2_sql
from os.path import join, dirname, realpath

from ll.util.config_db import db_conn


def flatten(i, filter=True):
    return [i] if not isinstance(i, list) else [k for j in i for k in flatten(j) if not filter or k]


def file_date():
    today = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    return f"{today}_{re.findall('..:.*', str(datetime.datetime.now()))[0]}"


def get_json_from_file(filename):
    json_file = open(join(dirname(realpath(__file__)), '../../json', filename), 'r')
    json_config = jstyleson.load(json_file)
    json_file.close()

    return json_config


def get_string_from_sql(sql):
    with db_conn() as conn:
        return sql.as_string(conn)


def n3_pred_val(predicate, value, end=False, line=True):
    new_line = '\n' if line is True else ''
    tab = '\t' if line is True else ''
    return f"{tab}{predicate:{40}} {value} {'.' if end is True else ';'}{new_line}"


def get_id_of_uri(uri):
    local = re.findall(".*[/#:](.*)$", uri)
    if len(local) > 0 and len(local[0]) > 0:
        return local[0]

    bad_uri = re.findall("(.*)[/#:]$", uri)
    if len(bad_uri) > 0:
        return get_id_of_uri(bad_uri[0])

    return uri


def get_sql_empty(sql, add_new_line=True):
    if not sql or sql == psycopg2_sql.SQL('') or sql == psycopg2_sql.Composed([]):
        return psycopg2_sql.SQL('')

    return psycopg2_sql.Composed([psycopg2_sql.SQL('\n'), sql]) if add_new_line else sql


def get_pagination_sql(limit=None, offset=0):
    return ('LIMIT ' + str(limit) + ' ' if limit else '') + ('OFFSET ' + str(offset) if offset > 0 else '')


def get_association_files():
    return []
