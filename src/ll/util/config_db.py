import os

from contextlib import contextmanager
from psycopg2 import extras as psycopg2_extras
from psycopg2.pool import ThreadedConnectionPool

conn_pool = ThreadedConnectionPool(
    minconn=2,
    maxconn=20,
    host=os.environ.get('DATABASE_HOST', 'localhost'),
    port=os.environ.get('DATABASE_PORT', 5432),
    database=os.environ.get('DATABASE_DB', 'postgres'),
    user=os.environ.get('DATABASE_USER', 'postgres'),
    password=os.environ.get('DATABASE_PASSWORD', 'postgres'),
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


def fetch_one(query, args=None, dict=False):
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) if dict else conn.cursor() as cur:
            cur.execute(query, args)
            return cur.fetchone() if cur.description else None


def fetch_many(cur, size=2000):
    while True:
        results = cur.fetchmany(size=size)
        if not results:
            break

        for result in results:
            yield result
