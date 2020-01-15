import re
import datetime
import jstyleson

from hashlib import md5
from os.path import join, dirname, realpath

from ll.util.config_db import db_conn


def hasher(object):
    h = md5()
    h.update(bytes(object.__str__(), encoding='utf-8'))
    return F"H{h.hexdigest()[:15]}"


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


def hash_string(to_hash):
    return md5(to_hash.encode('utf-8')).hexdigest()


def is_nt_format(resource):
    temp = resource.strip()
    return temp.startswith('<') and temp.endswith('>')


def to_nt_format(resource):
    if is_nt_format(resource):
        return resource

    return '<{}>'.format(resource)


def get_pagination_sql(limit=None, offset=0):
    return ('LIMIT ' + str(limit) + ' ' if limit else '') + ('OFFSET ' + str(offset) if offset > 0 else '')


def get_association_files():
    return []
