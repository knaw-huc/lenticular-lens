import json
import os
import psycopg2
from psycopg2 import sql as psycopg2_sql
from typing import List, Mapping, Sequence


def config_db():
    return json.loads(os.environ['DATABASE_CONFIG'])


def db_conn():
    return psycopg2.connect(**config_db())


def execute_query(query_dict: Mapping, cursor_args: Mapping = None) -> List[Sequence]:
    """
    Execute a query using the default database connection and return all results.

    :param query_dict: a dictionary containing:
        'query': a query string or a psycopg2.sql.Composable
        'parameters' (optional): the parameters to pass to cursor.execute() (a tuple, list, or dict)
    :param cursor_args: a dictionary containing the arguments to pass to the cursor constructor.
    :return: a list containing the rows returned by the query (as tuples by default)
    """
    if not cursor_args:
        cursor_args = {}

    if 'parameters' not in query_dict:
        setattr(query_dict, 'parameters', None)

    conn = db_conn()
    with conn, conn.cursor(**cursor_args) as cur:
        cur.execute(query_dict['query'], query_dict['parameters'])

        return cur.fetchall() if not query_dict['header'] else [query_dict['header']] + cur.fetchall()


def run_query(query, args=None):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(query, args)
    result = cur.fetchone() if cur.description else None
    conn.commit()
    conn.close()
    return result


def table_exists(table_name):
    return run_query(psycopg2_sql.SQL("SELECT to_regclass({});").format(psycopg2_sql.Literal(table_name)))[0] is not None
