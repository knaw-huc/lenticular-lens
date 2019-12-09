import os
from contextlib import contextmanager
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


def fetch_one(query, args=None, dict=False):
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) if dict else conn.cursor() as cur:
            cur.execute(query, args)
            return cur.fetchone() if cur.description else None
