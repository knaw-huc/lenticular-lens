from psycopg2 import extras
from ll.util.config_db import db_conn

from ll.util.helpers import get_yaml_from_file

internal_transformers_info = get_yaml_from_file('internal_transformers')

filter_functions = dict()
matching_methods = dict()
transformers = dict()


def reset():
    filter_functions.clear()
    matching_methods.clear()
    transformers.clear()


def get_filter_functions():
    if not filter_functions:
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT key, config FROM filter_functions')

            for filter_function in cur:
                filter_functions[filter_function['key']] = filter_function['config']

    return filter_functions


def get_matching_methods():
    if not matching_methods:
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT key, config FROM matching_methods')

            for matching_method in cur:
                matching_methods[matching_method['key']] = matching_method['config']

    return matching_methods


def get_transformers():
    if not transformers:
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT key, config FROM transformers')

            for transformer in cur:
                transformers[transformer['key']] = transformer['config']

        for (key, config) in internal_transformers_info.items():
            transformers[key] = {'internal': True} | config

    return transformers
