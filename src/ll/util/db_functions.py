import json

from psycopg2 import extras
from collections import OrderedDict
from ll.util.config_db import db_conn

from ll.util.helpers import get_yaml_from_file

internal_transformers_info = get_yaml_from_file('internal_transformers')

filter_functions = OrderedDict()
matching_methods = OrderedDict()
transformers = OrderedDict()


def reset():
    filter_functions.clear()
    matching_methods.clear()
    transformers.clear()


def get_filter_functions():
    if not filter_functions:
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT key, config::text FROM filter_functions ORDER BY (config->>'order')::int")

            for filter_function in cur:
                filter_functions[filter_function['key']] = \
                    json.loads(filter_function['config'], object_pairs_hook=OrderedDict)

    return filter_functions


def get_matching_methods():
    if not matching_methods:
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT key, config::text FROM matching_methods ORDER BY (config->>'order')::int")

            for matching_method in cur:
                matching_methods[matching_method['key']] = \
                    json.loads(matching_method['config'], object_pairs_hook=OrderedDict)

    return matching_methods


def get_transformers():
    if not transformers:
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT key, config::text FROM transformers ORDER BY (config->>'order')::int")

            for transformer in cur:
                transformers[transformer['key']] = \
                    json.loads(transformer['config'], object_pairs_hook=OrderedDict)

        for (key, config) in internal_transformers_info.items():
            transformers[key] = {**{'internal': True}, **config}

    return transformers


def get_all_jobs():
    with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute("SELECT job_id, job_title, job_description, job_link, "
                    "created_at, updated_at, 'owner' AS role FROM jobs")
        return cur.fetchall()
