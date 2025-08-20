from os import environ
from json import loads
from logging import getLogger

from socketio import AsyncServer
from asyncio import create_task, Queue
from contextlib import asynccontextmanager

from lenticularlens.util.db_functions import reset
from lenticularlens.util.config_db import listen_for_notify

log = getLogger(__name__)
enable_logger = environ.get('LOG_LEVEL', 'INFO').upper() == 'DEBUG'

sio = AsyncServer(cors_allowed_origins='*', namespaces='*', async_mode='asgi',
                  logger=enable_logger, engineio_logger=enable_logger)


async def emit_database_events(queue: Queue):
    while True:
        notify = await queue.get()
        if notify.channel == 'extension_update':
            reset()

        ns = '' if (notify.channel == 'extension_update' or
                    notify.channel.startswith('timbuctoo_') or notify.channel.startswith('sparql_')) \
            else loads(notify.payload)['job_id']

        await sio.emit(notify.channel, notify.payload, namespace=f'/{ns}')
        queue.task_done()

        log.debug(f'WebSocket emit on /{ns}: {notify.channel} = {notify.payload}')


@asynccontextmanager
async def fastapi_lifespan(_app):
    queue = Queue()
    listener_task = create_task(listen_for_notify(queue))
    emitter_task = create_task(emit_database_events(queue))

    yield

    emitter_task.cancel()
    listener_task.cancel()
    queue.shutdown()
