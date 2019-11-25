import os

from contextlib import contextmanager
from typing import List, Mapping, Sequence

from psycopg2 import extras as psycopg2_extras
from psycopg2.pool import ThreadedConnectionPool

conn_pool = ThreadedConnectionPool(
    minconn=2,
    maxconn=6,
    host=os.environ['DATABASE_HOST'] if 'DATABASE_HOST' in os.environ else 'localhost',
    port=os.environ['DATABASE_PORT'] if 'DATABASE_PORT' in os.environ else 5432,
    database=os.environ['DATABASE_DB'] if 'DATABASE_DB' in os.environ else 'postgres',
    user=os.environ['DATABASE_USER'] if 'DATABASE_USER' in os.environ else 'postgres',
    password=os.environ['DATABASE_PASSWORD'] if 'DATABASE_PASSWORD' in os.environ else 'postgres',
)


def get_conn(key=None):
    return conn_pool.getconn(key)


def return_conn(conn, key=None):
    conn_pool.putconn(conn, key)


@contextmanager
def db_conn(key=None):
    try:
        with get_conn(key) as conn:
            yield conn
    finally:
        return_conn(conn, key)


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


def fetch_one(query, args=None, dict=False):
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) if dict else conn.cursor() as cur:
            cur.execute(query, args)
            return cur.fetchone() if cur.description else None
