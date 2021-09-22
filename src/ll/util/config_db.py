import os

from contextlib import contextmanager
from eventlet.hubs import trampoline

from psycopg2 import extras
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn_pool = ThreadedConnectionPool(
    minconn=2,
    maxconn=int(os.environ.get('DATABASE_MAX_CONNECTIONS', 5)),
    host=os.environ.get('DATABASE_HOST', 'localhost'),
    port=int(os.environ.get('DATABASE_PORT', 5432)),
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
    with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) if dict else conn.cursor() as cur:
        cur.execute(query, args)
        return cur.fetchone() if cur.description else None


def fetch_many(cur, size=2000):
    while True:
        results = cur.fetchmany(size=size)
        if not results:
            break

        for result in results:
            yield result


def listen_for_notify(q):
    conn = get_conn()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    cur.execute('LISTEN job_update; '
                'LISTEN timbuctoo_update; LISTEN alignment_update; LISTEN clustering_update; '
                'LISTEN timbuctoo_delete; LISTEN alignment_delete; LISTEN clustering_delete;')

    while True:
        trampoline(conn, read=True)
        conn.poll()
        while conn.notifies:
            q.put(conn.notifies.pop())
