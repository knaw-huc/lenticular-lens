import os
import psycopg2

from typing import List, Mapping, Sequence
from psycopg2 import sql as psycopg2_sql, extras as psycopg2_extras


def config_db():
    return {
        "host": os.environ['DATABASE_HOST'] if 'DATABASE_HOST' in os.environ else "localhost",
        "port": os.environ['DATABASE_PORT'] if 'DATABASE_PORT' in os.environ else 5432,
        "database": os.environ['DATABASE_DB'] if 'DATABASE_DB' in os.environ else "postgres",
        "user": os.environ['DATABASE_USER'] if 'DATABASE_USER' in os.environ else "postgres",
        "password": os.environ['DATABASE_PASSWORD'] if 'DATABASE_PASSWORD' in os.environ else "postgres",
    }


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

    with db_conn() as conn, conn.cursor(**cursor_args) as cur:
        cur.execute(query_dict['query'], query_dict['parameters'])

        return cur.fetchall() if 'header' not in query_dict or not query_dict['header'] \
            else [query_dict['header']] + cur.fetchall()


def run_query(query, args=None, dict=False):
    conn = db_conn()
    cur = conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) if dict else conn.cursor()
    cur.execute(query, args)
    result = cur.fetchone() if cur.description else None
    conn.commit()
    conn.close()
    return result


def table_exists(table_name):
    return run_query(psycopg2_sql.SQL("SELECT to_regclass({});")
                     .format(psycopg2_sql.Literal(table_name)))[0] is not None
