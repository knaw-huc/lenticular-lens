import os

from eventlet.hubs import trampoline
from psycopg_pool import ConnectionPool

conn_pool = ConnectionPool(
    conninfo='host={} port={} dbname={} user={} password={}'.format(
        os.environ.get('DATABASE_HOST', 'localhost'),
        os.environ.get('DATABASE_PORT', ' 5432'),
        os.environ.get('DATABASE_DB', 'postgres'),
        os.environ.get('DATABASE_USER', 'postgres'),
        os.environ.get('DATABASE_PASSWORD', 'postgres')
    ),
    min_size=4,
    max_size=int(os.environ.get('DATABASE_MAX_CONNECTIONS', 5)),
)


def fetch_many(cur, size=2000):
    while True:
        results = cur.fetchmany(size=size)
        if not results:
            break

        for result in results:
            yield result


def listen_for_notify(q):
    def notifies_without_blocking(conn):
        import psycopg

        with conn.lock:
            enc = conn.pgconn._encoding
            try:
                ns = conn.wait(psycopg.generators.notifies(conn.pgconn))
            except psycopg.errors._NO_TRACEBACK as ex:
                raise ex.with_traceback(None)

        for pgn in ns:
            n = psycopg.connection.Notify(pgn.relname.decode(enc), pgn.extra.decode(enc), pgn.be_pid)
            yield n

    conn = conn_pool.getconn()
    conn.autocommit = True
    conn.execute('LISTEN extension_update; LISTEN job_update; '
                 'LISTEN timbuctoo_update; LISTEN alignment_update; LISTEN clustering_update; '
                 'LISTEN timbuctoo_delete; LISTEN alignment_delete; LISTEN clustering_delete;')

    while True:
        trampoline(conn, read=True)
        gen = notifies_without_blocking(conn)  # TODO: conn.notifies()
        for notify in gen:
            q.put(notify)
