from os import environ
from asyncio import Queue
from psycopg import AsyncConnection
from psycopg_pool import ConnectionPool

conn_info = 'host={} port={} dbname={} user={} password={}'.format(
    environ.get('DATABASE_HOST', 'localhost'),
    environ.get('DATABASE_PORT', ' 5432'),
    environ.get('DATABASE_DB', 'postgres'),
    environ.get('DATABASE_USER', 'postgres'),
    environ.get('DATABASE_PASSWORD', 'postgres')
)

conn_pool = ConnectionPool(
    conninfo=conn_info,
    min_size=4,
    max_size=int(environ.get('DATABASE_MAX_CONNECTIONS', 5)),
)


def fetch_many(cur, size=2000):
    while True:
        results = cur.fetchmany(size=size)
        if not results:
            break

        for result in results:
            yield result


async def listen_for_notify(queue: Queue):
    conn = await AsyncConnection.connect(conn_info, autocommit=True)
    await conn.execute('LISTEN extension_update; LISTEN job_update; '
                       'LISTEN sparql_delete; LISTEN timbuctoo_delete; '
                       'LISTEN sparql_load_update; LISTEN sparql_load_delete; '
                       'LISTEN sparql_status_update; LISTEN timbuctoo_status_update; '
                       'LISTEN sparql_update; LISTEN timbuctoo_update; '
                       'LISTEN alignment_update; LISTEN clustering_update; '
                       'LISTEN alignment_delete; LISTEN clustering_delete;')

    async for notify in conn.notifies():
        await queue.put(notify)
