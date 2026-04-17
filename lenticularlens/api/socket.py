from os import environ
from json import loads
from logging import getLogger

from psycopg import Notify
from socketio import AsyncServer
from asyncio import create_task, CancelledError
from contextlib import asynccontextmanager

from lenticularlens.util.db_functions import reset
from lenticularlens.util.config_db import listen_for_notify

log = getLogger(__name__)
enable_logger = environ.get('LOG_LEVEL', 'INFO').upper() == 'DEBUG'

sio = AsyncServer(cors_allowed_origins='*', namespaces='*', async_mode='asgi',
                  logger=enable_logger, engineio_logger=enable_logger)


async def start_listener():
    await listen_for_notify(handle_notify)


async def handle_notify(notify: Notify):
    if notify.channel == 'extension_update':
        reset()

    ns = '' if (notify.channel == 'extension_update' or
                notify.channel.startswith('timbuctoo_') or notify.channel.startswith('sparql_')) \
        else loads(notify.payload)['job_id']

    await sio.emit(notify.channel, notify.payload, namespace=f'/{ns}')

    log.debug(f'WebSocket emit on /{ns}: {notify.channel} = {notify.payload}')


@asynccontextmanager
async def fastapi_lifespan(_app):
    task = create_task(start_listener())

    yield

    task.cancel()
    try:
        await task
    except CancelledError:
        pass
