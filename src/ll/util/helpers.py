import os
import re
import json
import datetime

from psycopg2 import sql
from collections import OrderedDict
from os.path import join, dirname, realpath

from ll.util.config_db import db_conn


def get_publisher():
    return os.environ.get('PUBLISHER', 'Lenticular Lens')


def flatten(i, filter=True):
    return [i] if not isinstance(i, list) else [k for j in i for k in flatten(j) if not filter or k]


def file_date():
    today = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    return f"{today}_{re.findall('..:.*', str(datetime.datetime.now()))[0]}"


def get_json_from_file(filename):
    json_file = open(join(dirname(realpath(__file__)), '../../json', filename), 'r')
    json_config = json.load(json_file, object_pairs_hook=OrderedDict)
    json_file.close()

    return json_config


def get_string_from_sql(sql):
    with db_conn() as conn:
        return sql.as_string(conn)


def get_id_of_uri(uri):
    local = re.findall(".*[/#:](.*)$", uri)
    if len(local) > 0 and len(local[0]) > 0:
        return local[0]

    bad_uri = re.findall("(.*)[/#:]$", uri)
    if len(bad_uri) > 0:
        return get_id_of_uri(bad_uri[0])

    return uri


def get_sql_empty(sql_insert, flag=True, prefix=None, suffix=None, add_new_line=True):
    if not flag or not sql_insert or sql_insert == sql.SQL('') or sql_insert == sql.Composed([]):
        return sql.SQL('')

    sql_composed = [sql_insert]
    if prefix:
        sql_composed.insert(0, prefix)
    if suffix:
        sql_composed.append(suffix)
    if add_new_line:
        sql_composed.insert(0, sql.SQL('\n'))

    return sql.Composed(sql_composed) if len(sql_composed) > 1 else sql_insert


def get_pagination_sql(limit=None, offset=0):
    return ('LIMIT ' + str(limit) + ' ' if limit else '') + ('OFFSET ' + str(offset) if offset > 0 else '')


def get_from_buffer(buffer):
    buffer.seek(0)
    text = buffer.read()

    buffer.truncate(0)
    buffer.seek(0)

    return text
