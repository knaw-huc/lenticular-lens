import re
import datetime
import jstyleson

from psycopg2 import sql as psycopg2_sql
from os.path import join, dirname, realpath

from ll.util.config_db import db_conn


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


def is_nt_format(resource):
    temp = resource.strip()
    return temp.startswith('<') and temp.endswith('>')


def to_nt_format(resource):
    if is_nt_format(resource):
        return resource

    return '<{}>'.format(resource)


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
